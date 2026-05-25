import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core"
USER = ROOT / "samples" / "m2m" / "user"
DEV = ROOT / "samples" / "m2m" / "dev"

STATE_ORDER: List[str] = [
    "INIT",
    "TERMS_ACCEPTED",
    "APP_ACTIVATED",
    "ALIVE_HOME",
    "SECURITY_SELECTED",
    "TRANSLATE_SUCCESS",
    "QUEUE_JOINED",
    "MATCH_FOUND",
    "ROOM_CONNECTED",
    "RECONNECTING",
    "ROOM_RECOVERED",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        if default is None:
            raise FileNotFoundError(path)
        write_json(path, default)
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(event: str, state: str, note: str = "", payload: Dict[str, Any] | None = None) -> None:
    log_path = CORE / "session_log.json"
    data = read_json(log_path, {"system": "KRXA", "logs": []})
    data.setdefault("logs", []).append({
        "ts": now(),
        "event": event,
        "state": state,
        "note": note,
        "payload": payload or {},
    })
    write_json(log_path, data)


class StateEngine:
    def __init__(self) -> None:
        self.control_path = CORE / "control_state.json"
        self.session_path = USER / "session_state.json"
        self.queue_path = USER / "queue_state.json"
        self.presence_path = USER / "presence_state.json"
        self.reconnect_path = USER / "reconnect_state.json"
        self.recovery_path = USER / "recovery_state.json"
        self.message_path = USER / "message_state.json"

    def current_state(self) -> str:
        control = read_json(self.control_path)
        return control.get("current_state", "INIT")

    def set_state(self, next_state: str, reason: str = "manual") -> str:
        if next_state not in STATE_ORDER:
            self.record_failure(f"UNKNOWN_STATE:{next_state}", self.current_state())
            raise ValueError(f"Unknown state: {next_state}")
        control = read_json(self.control_path)
        old_state = control.get("current_state", "INIT")
        control["previous_state"] = old_state
        control["current_state"] = next_state
        control["status"] = "RUNNING"
        control["updated_at"] = now()
        write_json(self.control_path, control)
        session = read_json(self.session_path)
        session["session_state"] = next_state
        session.setdefault("state_history", []).append({"ts": now(), "from": old_state, "to": next_state, "reason": reason})
        self._apply_flags(session, next_state)
        write_json(self.session_path, session)
        append_log("STATE_TRANSITION", next_state, f"{old_state} -> {next_state}", {"reason": reason})
        return next_state

    def advance(self, reason: str = "advance") -> str:
        current = self.current_state()
        try:
            idx = STATE_ORDER.index(current)
        except ValueError:
            self.record_failure(f"INVALID_CURRENT_STATE:{current}", current)
            idx = 0
        next_state = STATE_ORDER[min(idx + 1, len(STATE_ORDER) - 1)]
        return self.set_state(next_state, reason)

    def run_until(self, target: str) -> str:
        if target not in STATE_ORDER:
            raise ValueError(f"Unknown target state: {target}")
        while STATE_ORDER.index(self.current_state()) < STATE_ORDER.index(target):
            self.advance("run_until")
        return self.current_state()

    def reset(self) -> None:
        self.set_state("INIT", "reset")
        write_json(self.queue_path, {"queue_state": "EMPTY", "users_waiting": [], "match_found": False})
        write_json(self.presence_path, {"presence_state": "OFFLINE", "heartbeat": None, "last_seen": None})
        write_json(self.reconnect_path, {"reconnect_state": "IDLE", "attempts": 0, "last_attempt": None})
        write_json(self.recovery_path, {"recovery_state": "CLEAN", "last_recovered_state": None, "recovery_log": []})
        write_json(self.message_path, {"message_state": "EMPTY", "last_message": None, "history": []})
        append_log("ENGINE_RESET", "INIT", "KRXA engine reset complete")

    def heartbeat(self) -> None:
        data = read_json(self.presence_path)
        data["presence_state"] = "ONLINE"
        data["heartbeat"] = now()
        data["last_seen"] = now()
        write_json(self.presence_path, data)
        append_log("PRESENCE_HEARTBEAT", self.current_state(), "presence online")

    def queue_join(self, user_id: str = "user_A") -> None:
        data = read_json(self.queue_path)
        data["queue_state"] = "WAITING"
        if user_id not in data.setdefault("users_waiting", []):
            data["users_waiting"].append(user_id)
        data["match_found"] = len(data["users_waiting"]) >= 1
        write_json(self.queue_path, data)
        self.set_state("QUEUE_JOINED", "queue_join")

    def match_room(self, room_id: str = "room_local_001") -> None:
        queue = read_json(self.queue_path)
        queue["queue_state"] = "MATCHED"
        queue["match_found"] = True
        queue["room_id"] = room_id
        write_json(self.queue_path, queue)
        self.set_state("MATCH_FOUND", "match_room")
        self.set_state("ROOM_CONNECTED", "room_connected")

    def reconnect_and_recover(self) -> None:
        reconnect = read_json(self.reconnect_path)
        reconnect["reconnect_state"] = "RECONNECTING"
        reconnect["attempts"] = reconnect.get("attempts", 0) + 1
        reconnect["last_attempt"] = now()
        write_json(self.reconnect_path, reconnect)
        self.set_state("RECONNECTING", "network_reconnect")
        recovery = read_json(self.recovery_path)
        recovery["recovery_state"] = "RECOVERED"
        recovery["last_recovered_state"] = "ROOM_CONNECTED"
        recovery.setdefault("recovery_log", []).append({"ts": now(), "from": "RECONNECTING", "to": "ROOM_RECOVERED"})
        write_json(self.recovery_path, recovery)
        self.set_state("ROOM_RECOVERED", "recovery_complete")

    def record_message(self, source: str, target: str, text: str, converted: str) -> None:
        msg = read_json(self.message_path, {"message_state":"EMPTY","last_message":None,"history":[]})
        item = {"ts": now(), "source": source, "target": target, "input": text, "output": converted}
        msg["message_state"] = "DELIVERED"
        msg["last_message"] = item
        msg.setdefault("history", []).append(item)
        write_json(self.message_path, msg)
        append_log("MESSAGE_DELIVERED", self.current_state(), "local m2m message delivered", item)

    def record_failure(self, error: str, state: str) -> None:
        recovery = read_json(self.recovery_path, {"recovery_state":"DIRTY","last_recovered_state":None,"recovery_log":[]})
        recovery["recovery_state"] = "DIRTY"
        recovery.setdefault("recovery_log", []).append({"ts": now(), "state": state, "error": error})
        write_json(self.recovery_path, recovery)
        append_log("ENGINE_FAILURE", state, error)

    def _apply_flags(self, session: Dict[str, Any], state: str) -> None:
        flow = session.setdefault("user_flow", {})
        flags = {
            "TERMS_ACCEPTED": "terms",
            "APP_ACTIVATED": "app_activated",
            "ALIVE_HOME": "alive_home",
            "SECURITY_SELECTED": "security_selected",
            "TRANSLATE_SUCCESS": "translation_success",
            "ROOM_CONNECTED": "room_connected",
            "ROOM_RECOVERED": "room_connected",
        }
        if state in flags:
            flow[flags[state]] = True
