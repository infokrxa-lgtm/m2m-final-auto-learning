from __future__ import annotations

import json
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.state_engine import write_json
from scripts.input_flow import run_input_flow, USER

HOST = "127.0.0.1"
PORT = 8787

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send_json({"ok": True})

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            return self._send_json({"ok": True, "engine": "KRXA_REALTIME", "state": "READY"})
        if path == "/api/result":
            p = USER / "input_result.json"
            if p.exists():
                return self._send_json(json.loads(p.read_text(encoding="utf-8")))
            return self._send_json({"ok": False, "message": "no result yet"}, 404)
        return super().do_GET()

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/input-flow":
            return self._send_json({"ok": False, "error": "not found"}, 404)
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8")
            payload = json.loads(raw or "{}")
            input_state = {
                "schema": "KRXA_INPUT_STATE_V1",
                "source": "realtime_ui",
                "session_id": payload.get("session_id", "realtime_ui_local"),
                "from": payload.get("from", "user_A"),
                "to": payload.get("to", "user_B"),
                "source_lang": payload.get("source_lang", "ko"),
                "target_lang": payload.get("target_lang", "en"),
                "mode": payload.get("mode", "m2m"),
                "text": payload.get("text", "안녕하세요"),
            }
            write_json(USER / "input_state.json", input_state)
            result = run_input_flow()
            return self._send_json({"ok": True, "result": result})
        except Exception as exc:
            return self._send_json({"ok": False, "error": str(exc)}, 500)

if __name__ == "__main__":
    print("KRXA REALTIME ENGINE: READY")
    print(f"OPEN: http://{HOST}:{PORT}/samples/m2m/user/user_ui.html")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
