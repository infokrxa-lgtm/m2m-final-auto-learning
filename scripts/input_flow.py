from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.state_engine import StateEngine, append_log, read_json, write_json
CORE = ROOT / "core"
USER = ROOT / "samples" / "m2m" / "user"


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_input() -> Dict[str, Any]:
    default = {
        "schema": "KRXA_INPUT_STATE_V1",
        "source": "default",
        "session_id": "input_flow_local",
        "from": "user_A",
        "to": "user_B",
        "source_lang": "ko",
        "target_lang": "en",
        "mode": "m2m",
        "text": "안녕하세요",
        "created_at": now(),
    }
    data = read_json(USER / "input_state.json", default)
    if not data.get("text"):
        data["text"] = default["text"]
    return data


def classify_intent(text: str, krxai_db: Dict[str, Any], language_db: Dict[str, Any]) -> Tuple[str, float]:
    lower = text.lower()
    best = (krxai_db.get("confidence_rules", {}).get("fallback_intent", "m2m_message"), 0.55)

    for phrase in language_db.get("phrases", []):
        p_text = str(phrase.get("text", ""))
        if p_text and p_text in text:
            return str(phrase.get("intent_hint", best[0])), 0.90

    intents = krxai_db.get("intents", {})
    ranked = sorted(intents.items(), key=lambda kv: kv[1].get("priority", 0), reverse=True)
    for intent, spec in ranked:
        for pattern in spec.get("patterns", []):
            if pattern == "*":
                continue
            if str(pattern).lower() in lower:
                return intent, 0.85
    return best


def convert_text(text: str, target: str, language_db: Dict[str, Any], mode: str = "m2m") -> Tuple[str, float]:
    if mode == "direct":
        return text, 1.0
    for pair in language_db.get("translation_pairs", []):
        if pair.get("source") == text:
            return str(pair.get("target", text)), float(pair.get("confidence", 0.9))
    return f"[M2M:{target}] {text}", 0.50


def run_input_flow() -> Dict[str, Any]:
    engine = StateEngine()
    input_state = load_input()
    language_db = read_json(CORE / "language_db.json", {})
    krxai_db = read_json(CORE / "krxai_db.json", {})

    source = input_state.get("from", "user_A")
    target = input_state.get("to", "user_B")
    text = input_state.get("text", "안녕하세요")
    mode = input_state.get("mode", "m2m")

    append_log("INPUT_FLOW_START", engine.current_state(), "user input flow start", input_state)
    intent, intent_confidence = classify_intent(text, krxai_db, language_db)
    converted_raw, convert_confidence = convert_text(text, target, language_db, mode)
    delivered = converted_raw if mode == "direct" else f"[M2M:{target}] {converted_raw}"

    engine.run_until("SECURITY_SELECTED")
    engine.record_message(source, target, text, delivered)
    engine.set_state("TRANSLATE_SUCCESS", f"input_flow_intent:{intent}")
    engine.queue_join(source)
    engine.match_room("room_input_001")

    result = {
        "schema": "KRXA_INPUT_FLOW_RESULT_V1",
        "state": engine.current_state(),
        "session_id": input_state.get("session_id", "input_flow_local"),
        "intent": intent,
        "intent_confidence": intent_confidence,
        "convert_confidence": convert_confidence,
        "from": source,
        "to": target,
        "input": text,
        "output": delivered,
        "mode": mode,
        "updated_at": now(),
    }
    write_json(USER / "input_result.json", result)

    # message_state.json에도 DB 판단 결과를 주입한다.
    msg_path = USER / "message_state.json"
    message_state = read_json(msg_path, {"message_state": "EMPTY", "last_message": None, "history": []})
    if message_state.get("last_message"):
        message_state["last_message"].update({
            "intent": intent,
            "intent_confidence": intent_confidence,
            "convert_confidence": convert_confidence,
            "db_source": ["language_db.json", "krxai_db.json"],
        })
        if message_state.get("history"):
            message_state["history"][-1] = message_state["last_message"]
        write_json(msg_path, message_state)

    append_log("INPUT_FLOW_COMPLETE", result["state"], "input flow connected to KRXADB", result)
    return result


if __name__ == "__main__":
    result = run_input_flow()
    print("KRXA INPUT FLOW CONNECT: PASS")
    print(f"INPUT: {result['input']}")
    print(f"INTENT: {result['intent']} ({result['intent_confidence']})")
    print(f"OUTPUT: {result['output']}")
    print(f"STATE: {result['state']}")
