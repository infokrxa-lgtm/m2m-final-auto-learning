import os, json, html, uuid, time, shutil, sqlite3
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from openai import OpenAI

app = FastAPI(title="KRXA V53 DB Product")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = Path(".").resolve()
DATA = Path("storage")
DATA.mkdir(exist_ok=True)

DB_PATH = DATA / "krxa_v53.db"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

LIVE_WS = {}
LOGS = []

MODES = {
    "travel": "여행",
    "call": "통화",
    "youtube": "유튜브",
    "game": "게임",
    "field": "현장"
}

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            nickname TEXT,
            language TEXT,
            auth_type TEXT,
            created_at TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS devices (
            device_id TEXT PRIMARY KEY,
            user_id TEXT,
            device_info TEXT,
            created_at TEXT,
            last_seen TEXT
        );

        CREATE TABLE IF NOT EXISTS rooms (
            room_id TEXT PRIMARY KEY,
            owner_id TEXT,
            mode TEXT,
            title TEXT,
            state TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS room_users (
            room_id TEXT,
            user_id TEXT,
            joined_at TEXT,
            PRIMARY KEY (room_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS invites (
            invite_id TEXT PRIMARY KEY,
            room_id TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id TEXT,
            from_user TEXT,
            source TEXT,
            result_json TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            kind TEXT,
            message TEXT,
            created_at TEXT
        );
        """)

init_db()

def log(kind, message):
    LOGS.append({"time": now(), "kind": kind, "message": message})
    del LOGS[:-200]
    with db() as conn:
        conn.execute(
            "INSERT INTO logs(kind,message,created_at) VALUES(?,?,?)",
            (kind, message, now())
        )

def safe_path(p=""):
    target = (ROOT / p).resolve()
    if not str(target).startswith(str(ROOT)):
        raise ValueError("invalid path")
    return target

def row_to_dict(row):
    return dict(row) if row else None

def get_or_create_user(user_id=None, nickname="", language="auto", auth_type="guest"):
    if not user_id:
        user_id = new_id("guest")

    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE user_id=?", (user_id,)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO users(user_id,nickname,language,auth_type,created_at,last_seen) VALUES(?,?,?,?,?,?)",
                (user_id, nickname or user_id, language, auth_type, now(), now())
            )
        else:
            conn.execute(
                "UPDATE users SET last_seen=?, language=COALESCE(NULLIF(?,''), language) WHERE user_id=?",
                (now(), language, user_id)
            )

    return user_id

def register_device(user_id, device_id=None, device_info=""):
    if not device_id:
        device_id = new_id("device")

    with db() as conn:
        row = conn.execute("SELECT * FROM devices WHERE device_id=?", (device_id,)).fetchone()
        if not row:
            conn.execute(
                "INSERT INTO devices(device_id,user_id,device_info,created_at,last_seen) VALUES(?,?,?,?,?)",
                (device_id, user_id, device_info, now(), now())
            )
        else:
            conn.execute(
                "UPDATE devices SET user_id=?, last_seen=?, device_info=? WHERE device_id=?",
                (user_id, now(), device_info, device_id)
            )
    return device_id

def create_room(owner_id, mode="travel", title="KRXA Room"):
    room_id = new_id("room")
    invite_id = new_id("invite")

    with db() as conn:
        conn.execute(
            "INSERT INTO rooms(room_id,owner_id,mode,title,state,created_at) VALUES(?,?,?,?,?,?)",
            (room_id, owner_id, mode, title, "LIVE", now())
        )
        conn.execute(
            "INSERT OR IGNORE INTO room_users(room_id,user_id,joined_at) VALUES(?,?,?)",
            (room_id, owner_id, now())
        )
        conn.execute(
            "INSERT INTO invites(invite_id,room_id,created_at) VALUES(?,?,?)",
            (invite_id, room_id, now())
        )

    log("room", f"{room_id} created by {owner_id}")
    return room_id, invite_id

def join_room(user_id, room_id):
    with db() as conn:
        room = conn.execute("SELECT * FROM rooms WHERE room_id=?", (room_id,)).fetchone()
        if not room:
            return False
        conn.execute(
            "INSERT OR IGNORE INTO room_users(room_id,user_id,joined_at) VALUES(?,?,?)",
            (room_id, user_id, now())
        )
    log("join", f"{user_id} joined {room_id}")
    return True

def invite_to_room(invite_id):
    with db() as conn:
        row = conn.execute("SELECT room_id FROM invites WHERE invite_id=?", (invite_id,)).fetchone()
        return row["room_id"] if row else None

def room_participants(room_id):
    with db() as conn:
        rows = conn.execute("""
            SELECT u.* FROM users u
            JOIN room_users ru ON u.user_id = ru.user_id
            WHERE ru.room_id=?
        """, (room_id,)).fetchall()
        return [dict(r) for r in rows]

def load_history(room_id, limit=10):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM history WHERE room_id=? ORDER BY id DESC LIMIT ?",
            (room_id, limit)
        ).fetchall()
    return [dict(r) for r in reversed(rows)]

def save_history(room_id, from_user, source, result):
    with db() as conn:
        conn.execute(
            "INSERT INTO history(room_id,from_user,source,result_json,created_at) VALUES(?,?,?,?,?)",
            (room_id, from_user, source, json.dumps(result, ensure_ascii=False), now())
        )

def krxa_translate(text, target_lang="auto", room_id="default"):
    history = load_history(room_id, 10)
    prompt = f"""
KRXA internal interpreter engine.

Rules:
- UI shows only KRXA.
- You are not a participant.
- If same language, relay naturally.
- If different language, translate naturally for the target user.
- Output only the final sentence.
- No explanation.

target_lang: {target_lang}

history:
{json.dumps(history, ensure_ascii=False)}

input:
{text}
"""
    r = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.choices[0].message.content or text

async def broadcast(room_id, payload, exclude=None):
    for uid, ws in list(LIVE_WS.get(room_id, {}).items()):
        if uid == exclude:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            pass

@app.get("/")
def home():
    return {"ok": True, "version": "V53", "routes": ["/user", "/signup", "/login", "/app", "/control", "/dev"]}

@app.get("/health")
def health():
    return {"ok": True, "version": "V53-DB"}

@app.get("/admin")
def admin_redirect():
    return RedirectResponse("/control", status_code=302)

@app.get("/api/state")
def api_state():
    with db() as conn:
        users = conn.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]
        devices = conn.execute("SELECT COUNT(*) c FROM devices").fetchone()["c"]
        rooms = conn.execute("SELECT COUNT(*) c FROM rooms").fetchone()["c"]
        invites = conn.execute("SELECT COUNT(*) c FROM invites").fetchone()["c"]
        recent_logs = conn.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 80").fetchall()

    return {
        "ok": True,
        "version": "V53",
        "users": users,
        "devices": devices,
        "rooms": rooms,
        "invites": invites,
        "live_rooms": list(LIVE_WS.keys()),
        "modes": MODES,
        "logs": [dict(r) for r in recent_logs]
    }

@app.post("/api/register")
def api_register(
    nickname: str = Form(""),
    language: str = Form("auto"),
    guest_user_id: str = Form(""),
    device_id: str = Form(""),
    device_info: str = Form("")
):
    user_id = guest_user_id or new_id("user")
    get_or_create_user(user_id, nickname or user_id, language, "member")
    device_id = register_device(user_id, device_id, device_info)
    log("signup", f"{user_id} registered")
    return {"ok": True, "user_id": user_id, "device_id": device_id}

@app.post("/api/login")
def api_login(user_id: str = Form(...), language: str = Form("auto"), device_id: str = Form(""), device_info: str = Form("")):
    get_or_create_user(user_id, user_id, language, "member")
    device_id = register_device(user_id, device_id, device_info)
    return {"ok": True, "user_id": user_id, "device_id": device_id}

@app.post("/device/register")
def device_register(user_id: str = Form(...), device_id: str = Form(""), device_info: str = Form("")):
    get_or_create_user(user_id)
    device_id = register_device(user_id, device_id, device_info)
    return {"ok": True, "device_id": device_id}

@app.post("/api/create_room")
def api_create_room(user_id: str = Form(...), mode: str = Form("travel")):
    get_or_create_user(user_id)
    room_id, invite_id = create_room(user_id, mode, f"KRXA {MODES.get(mode, mode)}")
    return {
        "ok": True,
        "room_id": room_id,
        "invite_id": invite_id,
        "invite_url": f"/app?invite={invite_id}&mode={mode}"
    }

@app.post("/api/join")
def api_join(user_id: str = Form(...), room_id: str = Form(""), invite_id: str = Form(""), language: str = Form("auto")):
    get_or_create_user(user_id, user_id, language)
    if invite_id:
        room_id = invite_to_room(invite_id)
        if not room_id:
            return {"ok": False, "error": "invalid invite"}
    if not room_id:
        return {"ok": False, "error": "missing room_id"}
    return {"ok": join_room(user_id, room_id), "room_id": room_id}

@app.post("/api/stt")
async def stt(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            tr = client.audio.transcriptions.create(model=STT_MODEL, file=f)
        return {"ok": True, "text": tr.text}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@app.post("/api/tts")
def tts(text: str = Form(...)):
    audio = client.audio.speech.create(model=TTS_MODEL, voice="alloy", input=text)
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.get("/history")
def history(room_id: str = "default"):
    return {"ok": True, "room_id": room_id, "history": load_history(room_id, 100)}

@app.websocket("/ws/room")
async def ws_room(ws: WebSocket):
    await ws.accept()

    user_id = ws.query_params.get("user_id") or new_id("guest")
    language = ws.query_params.get("language", "auto")
    mode = ws.query_params.get("mode", "travel")
    room_id = ws.query_params.get("room_id")
    invite_id = ws.query_params.get("invite_id")

    get_or_create_user(user_id, user_id, language, "guest")

    if invite_id and not room_id:
        room_id = invite_to_room(invite_id)

    if not room_id:
        room_id, invite_id = create_room(user_id, mode)
    else:
        join_room(user_id, room_id)

    LIVE_WS.setdefault(room_id, {})[user_id] = ws

    invite_url = ""
    with db() as conn:
        inv = conn.execute("SELECT invite_id FROM invites WHERE room_id=? LIMIT 1", (room_id,)).fetchone()
        if inv:
            invite_url = f"/app?invite={inv['invite_id']}&mode={mode}"

    await ws.send_json({
        "type": "joined",
        "user_id": user_id,
        "room_id": room_id,
        "participants": [p["user_id"] for p in room_participants(room_id)],
        "invite_url": invite_url
    })

    await broadcast(room_id, {
        "type": "presence",
        "participants": [p["user_id"] for p in room_participants(room_id)]
    }, exclude=user_id)

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text", "")
            if not text:
                continue

            participants = room_participants(room_id)
            delivered = []

            for target in participants:
                target_id = target["user_id"]
                if target_id == user_id:
                    continue

                translated = krxa_translate(text, target.get("language", "auto"), room_id)

                payload = {
                    "type": "message",
                    "from": user_id,
                    "source": text,
                    "translated": translated,
                    "mode": mode
                }

                target_ws = LIVE_WS.get(room_id, {}).get(target_id)
                if target_ws:
                    await target_ws.send_json(payload)

                delivered.append({"to": target_id, "translated": translated})

            result = {"delivered": delivered}
            save_history(room_id, user_id, text, result)

            await ws.send_json({"type": "sent", "source": text, "delivered": delivered})

    except WebSocketDisconnect:
        LIVE_WS.get(room_id, {}).pop(user_id, None)
        log("disconnect", f"{user_id} left {room_id}")

@app.get("/signup", response_class=HTMLResponse)
def signup_page():
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#071426;color:white;font-family:Arial}.wrap{max-width:430px;margin:auto;padding:24px}
input,select,button{width:100%;box-sizing:border-box;padding:14px;margin:8px 0;border-radius:12px}
button{background:#2363ff;color:white;border:0;font-weight:bold}
</style></head><body><div class="wrap">
<h1>KRXA 가입</h1>
<p>최소 정보만 입력합니다. 기존 게스트 사용 기록은 유지됩니다.</p>
<input id="nickname" placeholder="닉네임">
<select id="language"><option value="auto">언어 자동</option><option value="ko">한국어</option><option value="en">English</option><option value="ja">日本語</option></select>
<button onclick="signup()">가입하고 시작</button>
<p><a style="color:#8ab4ff" href="/user">게스트로 계속 사용</a></p>
<script>
async function signup(){
 const guest=localStorage.getItem("krxa_user_id") || "";
 const device=localStorage.getItem("krxa_device_id") || "";
 const fd=new FormData();
 fd.append("nickname",document.getElementById("nickname").value);
 fd.append("language",document.getElementById("language").value);
 fd.append("guest_user_id",guest);
 fd.append("device_id",device);
 fd.append("device_info",navigator.userAgent);
 const r=await fetch("/api/register",{method:"POST",body:fd});
 const j=await r.json();
 localStorage.setItem("krxa_user_id",j.user_id);
 localStorage.setItem("krxa_device_id",j.device_id);
 location.href="/user";
}
</script></div></body></html>
"""

@app.get("/login", response_class=HTMLResponse)
def login_page():
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{background:#071426;color:white;font-family:Arial}.wrap{max-width:430px;margin:auto;padding:24px}
input,select,button{width:100%;box-sizing:border-box;padding:14px;margin:8px 0;border-radius:12px}
button{background:#2363ff;color:white;border:0;font-weight:bold}
</style></head><body><div class="wrap">
<h1>KRXA 로그인</h1>
<input id="user_id" placeholder="사용자 ID">
<select id="language"><option value="auto">언어 자동</option><option value="ko">한국어</option><option value="en">English</option></select>
<button onclick="login()">로그인</button>
<script>
async function login(){
 const fd=new FormData();
 fd.append("user_id",document.getElementById("user_id").value);
 fd.append("language",document.getElementById("language").value);
 fd.append("device_id",localStorage.getItem("krxa_device_id")||"");
 fd.append("device_info",navigator.userAgent);
 const r=await fetch("/api/login",{method:"POST",body:fd});
 const j=await r.json();
 localStorage.setItem("krxa_user_id",j.user_id);
 localStorage.setItem("krxa_device_id",j.device_id);
 location.href="/user";
}
</script></div></body></html>
"""

@app.get("/user", response_class=HTMLResponse)
def user_ui():
    tabs = ""
    for k, v in MODES.items():
        tabs += f"<button onclick=\"openMode('{k}')\">{v}</button>"

    return f"""
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#071426;color:white;font-family:Arial}}
.wrap{{max-width:430px;margin:auto;min-height:100vh;padding:18px;box-sizing:border-box}}
.top{{text-align:center}}.core{{width:140px;height:140px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:18px auto;font-size:28px;font-weight:bold;box-shadow:0 0 24px #00d084;background:#0b1d36}}
.card{{background:#0b1d36;border:1px solid #18345a;border-radius:20px;padding:18px;margin:14px 0}}
button{{background:#2363ff;color:white;border:0;border-radius:14px;padding:14px 16px;margin:6px;font-weight:bold}}
.tabs{{display:flex;overflow-x:auto;white-space:nowrap}}.tabs button{{min-width:90px}}
a{{color:#8ab4ff}}
</style></head>
<body><div class="wrap">
<div class="top"><h1>KRXA 여행 통역</h1><p>사용자 A ⇄ 핸드폰 ⇄ 사용자 B</p><div class="core">KRXA</div></div>
<div class="card"><h3>시작</h3><button onclick="openMode('travel')">여행 통역 시작</button></div>
<div class="card"><h3>상황 선택</h3><div class="tabs">{tabs}</div></div>
<div class="card"><h3>계정</h3><p id="me"></p><a href="/signup">가입</a> | <a href="/login">로그인</a></div>
</div>
<script>
let uid=localStorage.getItem("krxa_user_id");
if(!uid){{uid="guest-"+Math.random().toString(16).slice(2,8);localStorage.setItem("krxa_user_id",uid);}}
let did=localStorage.getItem("krxa_device_id");
if(!did){{did="device-"+Math.random().toString(16).slice(2,8);localStorage.setItem("krxa_device_id",did);}}
document.getElementById("me").innerText="현재 ID: "+uid;
function openMode(m){{window.open('/app?mode='+m,'_blank');}}
</script>
</body></html>
"""

@app.get("/app", response_class=HTMLResponse)
def app_ui(mode: str = "travel", invite: str = ""):
    mode_label = MODES.get(mode, "여행")
    return f"""
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#071426;color:white;font-family:Arial}}
.wrap{{max-width:900px;margin:auto;padding:16px}}.card{{background:#0b1d36;border:1px solid #18345a;border-radius:16px;padding:16px;margin:12px 0}}
button{{background:#2363ff;color:white;border:0;border-radius:12px;padding:13px 16px;margin:5px;font-weight:bold}}
input,select,textarea{{width:100%;box-sizing:border-box;background:#07182d;color:white;border:1px solid #244a78;border-radius:12px;padding:12px;margin:5px 0}}
.core{{width:130px;height:130px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:18px auto;font-size:24px;font-weight:bold;box-shadow:0 0 24px #00d084}}
.box{{background:#102a4d;padding:12px;border-radius:12px;margin:8px 0}}
</style></head>
<body><div class="wrap">
<div class="card">
<h2>KRXA {mode_label}</h2><div class="core">KRXA</div>
<label>내 ID</label><input id="user_id">
<label>내 언어</label><select id="language"><option value="auto">자동</option><option value="ko">한국어</option><option value="en">English</option><option value="ja">日本語</option><option value="zh">中文</option><option value="es">Español</option></select>
<button onclick="createRoom()">초대 만들기</button><button onclick="joinInvite()">초대 입장</button><button onclick="connect()">연결 시작</button>
<input id="invite" value="{html.escape(invite)}" placeholder="invite_id"><input id="room_id" placeholder="room_id"><input id="invite_url" placeholder="초대 주소" readonly><p id="status">대기</p>
</div>
<div class="card">
<h3>대화</h3><textarea id="text">안녕하세요. 이 근처 지하철역이 어디인가요?</textarea>
<button onclick="send()">텍스트 전송</button><button onclick="recordTranslate()">음성 통역</button>
<div id="chat"></div><audio id="ttsAudio" controls></audio>
</div></div>
<script>
let ws=null;
let userId=localStorage.getItem("krxa_user_id") || ("guest-"+Math.random().toString(16).slice(2,8));
let deviceId=localStorage.getItem("krxa_device_id") || ("device-"+Math.random().toString(16).slice(2,8));
localStorage.setItem("krxa_user_id",userId);localStorage.setItem("krxa_device_id",deviceId);
document.getElementById("user_id").value=userId;
function log(t){{document.getElementById("chat").innerHTML+="<div class='box'>"+t+"</div>";}}
function status(t){{document.getElementById("status").innerText=t;}}
function uid(){{return document.getElementById("user_id").value;}}
function lang(){{return document.getElementById("language").value;}}
async function createRoom(){{
 localStorage.setItem("krxa_user_id",uid());
 const fd=new FormData();fd.append("user_id",uid());fd.append("mode","{mode}");
 const r=await fetch("/api/create_room",{{method:"POST",body:fd}});const j=await r.json();
 document.getElementById("room_id").value=j.room_id;document.getElementById("invite").value=j.invite_id;document.getElementById("invite_url").value=location.origin+j.invite_url;log("초대 생성: "+location.origin+j.invite_url);
}}
async function joinInvite(){{
 const fd=new FormData();fd.append("user_id",uid());fd.append("invite_id",document.getElementById("invite").value);fd.append("language",lang());
 const r=await fetch("/api/join",{{method:"POST",body:fd}});const j=await r.json();
 if(j.ok){{document.getElementById("room_id").value=j.room_id;log("입장 완료: "+j.room_id);}}else log("입장 실패: "+JSON.stringify(j));
}}
function connect(){{
 const room=document.getElementById("room_id").value;const invite=document.getElementById("invite").value;
 let url=(location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/room?user_id="+encodeURIComponent(uid())+"&language="+encodeURIComponent(lang())+"&mode={mode}";
 if(room)url+="&room_id="+encodeURIComponent(room);if(invite)url+="&invite_id="+encodeURIComponent(invite);
 ws=new WebSocket(url);
 ws.onmessage=(ev)=>{{const d=JSON.parse(ev.data);
  if(d.type==="joined"){{document.getElementById("room_id").value=d.room_id;if(d.invite_url)document.getElementById("invite_url").value=location.origin+d.invite_url;status("연결됨: "+d.room_id);log("KRXA 연결됨 / 참여자: "+d.participants.join(", "));}}
  if(d.type==="presence")log("참여자: "+d.participants.join(", "));
  if(d.type==="message"){{log("<b>"+d.from+" 원문:</b> "+d.source);log("<b>KRXA 통역:</b> "+d.translated);playTTS(d.translated);}}
  if(d.type==="sent"){{log("<b>나:</b> "+d.source);d.delivered.forEach(x=>log("<b>"+x.to+" 전달:</b> "+x.translated));}}
 }};
}}
function send(){{if(!ws||ws.readyState!==1){{alert("먼저 연결 시작");return;}}ws.send(JSON.stringify({{text:document.getElementById("text").value}}));}}
async function playTTS(text){{const fd=new FormData();fd.append("text",text);const r=await fetch("/api/tts",{{method:"POST",body:fd}});const blob=await r.blob();const url=URL.createObjectURL(blob);const a=document.getElementById("ttsAudio");a.src=url;a.play();}}
async function recordTranslate(){{const stream=await navigator.mediaDevices.getUserMedia({{audio:true}});const mr=new MediaRecorder(stream);let chunks=[];mr.ondataavailable=e=>chunks.push(e.data);mr.onstop=async()=>{{const blob=new Blob(chunks,{{type:"audio/webm"}});const fd=new FormData();fd.append("file",blob,"voice.webm");const sr=await fetch("/api/stt",{{method:"POST",body:fd}});const sj=await sr.json();document.getElementById("text").value=sj.text;send();}};mr.start();status("3초 녹음 중...");setTimeout(()=>{{mr.stop();status("녹음 완료");}},3000);}}
</script></body></html>
"""

@app.get("/control", response_class=HTMLResponse)
def control():
    state = api_state()

    buttons = ""
    for k, v in MODES.items():
        buttons += f"<button onclick=\"location.href='/app?mode={k}'\">{v}</button>"

    return f"""
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h1>KRXA V53 CONTROL</h1>
<p>
<a style="color:#8ab4ff" href="/user">USER</a> |
<a style="color:#8ab4ff" href="/dev">DEV</a> |
<a style="color:#8ab4ff" href="/api/state">STATE</a>
</p>
<h2>실행</h2>
{buttons}
<h2>DB 상태</h2>
<pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2, default=str))}</pre>
</body></html>
"""

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)
    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        return f"""
<html><body style="font-family:Arial;padding:20px">
<h2>KRXA DEV FILE EDIT</h2><p>{html.escape(path)}</p>
<form method="post" action="/dev/save"><input type="hidden" name="path" value="{html.escape(path)}">
<textarea name="content" style="width:100%;height:70vh;">{content}</textarea><br><button type="submit">SAVE</button></form>
<form method="post" action="/dev/delete"><input type="hidden" name="path" value="{html.escape(path)}"><button type="submit">DELETE</button></form>
<p><a href="/dev">FILE LIST</a> | <a href="/control">CONTROL</a></p></body></html>
"""
    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")
    return f"""
<html><body style="font-family:Arial;padding:20px">
<h2>KRXA DEV</h2><p><a href="/user">USER</a> | <a href="/control">CONTROL</a></p>
<h3>파일 생성</h3><form method="post" action="/dev/create"><input name="path" placeholder="new_file.py or folder/file.txt"><button type="submit">CREATE</button></form>
<ul>{''.join(items)}</ul></body></html>
"""

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    safe_path(path).write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)

@app.post("/dev/create")
def dev_create(path: str = Form(...)):
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("", encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)

@app.post("/dev/delete")
def dev_delete(path: str = Form(...)):
    target = safe_path(path)
    if target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)
    return RedirectResponse(url="/dev", status_code=303)

@app.get("/verify", response_class=HTMLResponse)
def verify():
    return """
<h2>KRXA V53 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user</a></li>
<li><a href="/signup">signup</a></li>
<li><a href="/login">login</a></li>
<li><a href="/app?mode=travel">app travel</a></li>
<li><a href="/control">control</a></li>
<li><a href="/dev">dev</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
