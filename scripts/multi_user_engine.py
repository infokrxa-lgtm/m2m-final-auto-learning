from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import json, sys, urllib.parse, os
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
USER_DIR = ROOT / 'samples' / 'm2m' / 'user'
CORE_DIR = ROOT / 'core'
ROOMS_FILE = USER_DIR / 'multi_room_state.json'
PORT = int(os.environ.get('PORT', '8788'))
HOST = os.environ.get('HOST', '127.0.0.1')

def load_json(path, default):
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except Exception:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def db_convert(text):
    lang = load_json(CORE_DIR / 'language_db.json', {})
    ai = load_json(CORE_DIR / 'krxai_db.json', {})
    t = (text or '').strip()
    intent = 'unknown'; confidence = 0.5; output = t
    # language_db mapping / phrase table friendly fallback
    mappings = lang.get('mappings') or lang.get('mapping') or {}
    pairs = mappings.get('ko_to_en') or mappings.get('ko_en') or mappings
    if isinstance(pairs, dict):
        for k, v in pairs.items():
            if k in t:
                output = v; intent = 'greeting' if '안녕' in k else 'translation'; confidence = 0.9
                break
    if intent == 'unknown' and ('안녕' in t or 'hello' in t.lower()):
        intent = 'greeting'; confidence = 0.9; output = 'Hello'
    responses = ai.get('responses', {})
    if intent in responses and isinstance(responses[intent], str):
        output = responses[intent]
    return intent, confidence, output

def initial_state():
    return {
        'schema': 'KRXA_MULTI_ROOM_STATE_V1',
        'state': 'READY',
        'rooms': {
            'room_default': {
                'room_id': 'room_default',
                'state': 'ROOM_CONNECTED',
                'users': ['user_A', 'user_B'],
                'messages': []
            }
        },
        'updated_at': datetime.now(timezone.utc).isoformat()
    }

def add_message(room_id, sender, receiver, text):
    state = load_json(ROOMS_FILE, initial_state())
    rooms = state.setdefault('rooms', {})
    room = rooms.setdefault(room_id, {'room_id': room_id, 'state': 'ROOM_CONNECTED', 'users': [], 'messages': []})
    users = room.setdefault('users', [])
    for u in [sender, receiver]:
        if u and u not in users:
            users.append(u)
    intent, confidence, converted = db_convert(text)
    msg = {
        'id': f"msg_{len(room.setdefault('messages', []))+1:04d}",
        'from': sender,
        'to': receiver,
        'input': text,
        'intent': intent,
        'confidence': confidence,
        'output': f'[M2M:{receiver}] {converted}',
        'created_at': datetime.now(timezone.utc).isoformat()
    }
    room['messages'].append(msg)
    room['state'] = 'ROOM_CONNECTED'
    state['state'] = 'ROOM_CONNECTED'
    state['updated_at'] = datetime.now(timezone.utc).isoformat()
    save_json(ROOMS_FILE, state)
    # mirror latest result for old UI/control UI
    save_json(USER_DIR / 'input_result.json', {
        'schema':'KRXA_INPUT_FLOW_RESULT_V1','state':'ROOM_CONNECTED','session_id':'multi_user_local',
        'intent': intent, 'confidence': confidence, 'from': sender, 'to': receiver,
        'input': text, 'output': msg['output'], 'updated_at': msg['created_at']
    })
    save_json(USER_DIR / 'message_state.json', msg)
    return msg, state

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin','*')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers(); self.wfile.write(body)
    def do_GET(self):
        if self.path.startswith('/api/state'):
            self._send_json(load_json(ROOMS_FILE, initial_state()))
        else:
            super().do_GET()
    def do_POST(self):
        if self.path.startswith('/api/send'):
            length = int(self.headers.get('Content-Length','0') or 0)
            data = json.loads(self.rfile.read(length).decode('utf-8') or '{}')
            msg, state = add_message(data.get('room_id','room_default'), data.get('from','user_A'), data.get('to','user_B'), data.get('text',''))
            self._send_json({'ok': True, 'message': msg, 'state': state})
        else:
            self._send_json({'ok': False, 'error':'not found'}, 404)

if __name__ == '__main__':
    save_json(ROOMS_FILE, load_json(ROOMS_FILE, initial_state()))
    print('KRXA MULTI USER ENGINE: READY')
    print(f'URL: http://{HOST}:{PORT}/samples/m2m/user/multi_user_ui.html')
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
