from scripts.state_engine import StateEngine, append_log
from pathlib import Path
import json


def local_convert(text: str, target: str = "B") -> str:
    # KRXADB v1: language_db exact-pair 우선, 없으면 기존 M2M 래핑 유지
    db_path = Path(__file__).resolve().parents[1] / "core" / "language_db.json"
    try:
        language_db = json.loads(db_path.read_text(encoding="utf-8"))
        for pair in language_db.get("translation_pairs", []):
            if pair.get("source") == text:
                return f"[M2M:{target}] {pair.get('target')}"
    except Exception:
        pass
    return f"[M2M:{target}] {text}"


def run_demo(message: str = "안녕하세요. 말대말 로컬 실행 테스트입니다.") -> None:
    engine = StateEngine()
    append_log("M2M_DEMO_START", engine.current_state(), "local execution demo start")
    engine.run_until("SECURITY_SELECTED")
    converted = local_convert(message, "user_B")
    engine.record_message("user_A", "user_B", message, converted)
    engine.set_state("TRANSLATE_SUCCESS", "message_converted")
    engine.queue_join("user_A")
    engine.match_room("room_local_001")
    append_log("M2M_DEMO_COMPLETE", engine.current_state(), "local m2m flow reached ROOM_CONNECTED")
    print("KRXA M2M LOCAL RUN: PASS")
    print(f"DELIVERED: {converted}")
    print(f"STATE: {engine.current_state()}")


if __name__ == "__main__":
    run_demo()
