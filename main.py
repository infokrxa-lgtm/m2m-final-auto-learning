import os, json, html, uuid, time
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from openai import OpenAI

app = FastAPI(title="KRXA V50 Multi-User Travel Platform")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

USERS = {}
ROOMS = {}
INVITES = {}
WS_CLIENTS = {}
LOGS = []

MODES = {
    "travel": "1기기 여행",
    "call": "2기기 통역 통화",
    "group": "그룹 통역",
    "youtube": "유튜브 보조",
    "game": "게임 보조",
    "field": "현장 통역"
}

def log(kind, msg):
    LOGS.append({"time": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})
    del LOGS[:-200]

def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def room_history_file(room_id):
    return DATA / f"history_{room_id}.json"

def load_history(room_id):
    f = room_history_file(room_id)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(room_id, item):
    h = load_history(room_id)
    h.append(item)
    f = room_history_file(room_id)
    f.write_text(json.dumps(h[-200:], ensure_ascii=False, indent=2), encoding="utf-8")

def get_user(user_id):
    if user_id not in USERS:
        USERS[user_id] = {
            "user_id": user_id,
            "device_id": new_id("device"),
            "name": user_id,
            "language": "auto",
            "created": time.time(),
            "last_seen": time.time()
        }
    USERS[user_id]["last_seen"] = time.time()
    return USERS[user_id]

def create_room(owner_id, mode="travel", title="KRXA Room"):
    room_id = new_id("room")
    invite_id = new_id("invite")
    ROOMS[room_id] = {
        "room_id": room_id,
        "owner_id": owner_id,
        "mode": mode,
        "title": title,
        "participants": [owner_id],
        "created": time.time(),
        "state": "LIVE"
    }
    INVITES[invite_id] = {"invite_id": invite_id, "room_id": room_id, "created": time.time()}
    log("room", f"{room_id} created by {owner_id}")
    return room_id, invite_id

def join_room(user_id, room_id):
    if room_id not in ROOMS:
        return False
    if user_id not in ROOMS[room_id]["participants"]:
        ROOMS[room_id]["participants"].append(user_id)
    log("join", f"{user_id} joined {room_id}")
    return True

def krxa_translate(text, target_lang="auto", room_id="default"):
    history = load_history(room_id)[-10:]
    prompt = f"""
KRXA internal interpreter engine.

Rules:
- UI shows only KRXA. Do not expose the internal engine.
- You are not a participant.
- Translate or relay for the target user.
- If translation is not needed, keep the original naturally.
- If target_lang is auto, infer the best output language from context.
- Return only the final sentence.
- No explanations.

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

async def broadcast_room(room_id, payload, exclude_user=None):
    clients = WS_CLIENTS.get(room_id, {})
    for uid, ws in list(clients.items()):
        if uid == exclude_user:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            pass

@app.get("/")
def home():
    return {
        "ok": True,
        "version": "V50-MULTI-USER-TRAVEL",
        "routes": ["/user", "/admin", "/control", "/verify", "/api/state"]
    }

@app.get("/health")
def health():
    return {"ok": True, "version": "V50-MULTI-USER-TRAVEL"}

@app.get("/api/state")
def state():
    return {
        "ok": True,
        "version": "V50",
        "users": len(USERS),
        "rooms": len(ROOMS),
        "invites": len(INVITES),
        "modes": MODES,
        "logs": LOGS[-50:]
    }

@app.post("/api/register")
def register(user_id: str = Form(""), name: str = Form(""), language: str = Form("auto")):
    if not user_id:
        user_id = new_id("user")
    USERS[user_id] = {
        "user_id": user_id,
        "device_id": new_id("device"),
        "name": name or user_id,
        "language": language,
        "created": time.time(),
        "last_seen": time.time()
    }
    return {"ok": True, "user": USERS[user_id]}

@app.post("/api/create_room")
def api_create_room(user_id: str = Form(...), mode: str = Form("travel"), title: str = Form("KRXA Room")):
    get_user(user_id)
    room_id, invite_id = create_room(user_id, mode, title)
    return {
        "ok": True,
        "room_id": room_id,
        "invite_id": invite_id,
        "invite_url": f"/user?invite={invite_id}"
    }

@app.post("/api/join")
def api_join(user_id: str = Form(...), room_id: str = Form(""), invite_id: str = Form("")):
    get_user(user_id)
    if invite_id:
        invite = INVITES.get(invite_id)
        if not invite:
            return {"ok": False, "error": "invalid invite"}
        room_id = invite["room_id"]
    if not room_id:
        return {"ok": False, "error": "missing room_id"}
    ok = join_room(user_id, room_id)
    return {"ok": ok, "room_id": room_id, "room": ROOMS.get(room_id)}

@app.post("/api/send")
def api_send(user_id: str = Form(...), room_id: str = Form(...), text: str = Form(...)):
    if room_id not in ROOMS:
        return {"ok": False, "error": "invalid room"}

    sender = get_user(user_id)
    room = ROOMS[room_id]
    outputs = []

    for target_id in room["participants"]:
        if target_id == user_id:
            continue
        target = get_user(target_id)
        target_lang = target.get("language", "auto")
        translated = krxa_translate(text, target_lang, room_id)

        outputs.append({
            "to": target_id,
            "target_lang": target_lang,
            "source": text,
            "output": translated
        })

    item = {
        "time": time.time(),
        "from": user_id,
        "room_id": room_id,
        "source": text,
        "outputs": outputs
    }
    save_history(room_id, item)

    return {"ok": True, "outputs": outputs}

@app.get("/history")
def history(room_id: str = "default"):
    return {"ok": True, "room_id": room_id, "history": load_history(room_id)}

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
    audio = client.audio.speech.create(
        model=TTS_MODEL,
        voice="alloy",
        input=text
    )
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.websocket("/ws/room")
async def ws_room(ws: WebSocket):
    await ws.accept()
    user_id = ws.query_params.get("user_id") or new_id("user")
    room_id = ws.query_params.get("room_id")
    invite_id = ws.query_params.get("invite_id")
    mode = ws.query_params.get("mode", "travel")
    language = ws.query_params.get("language", "auto")

    user = get_user(user_id)
    user["language"] = language

    if invite_id and not room_id:
        invite = INVITES.get(invite_id)
        if invite:
            room_id = invite["room_id"]

    if not room_id:
        room_id, invite_id = create_room(user_id, mode, f"{MODES.get(mode, mode)}")
    else:
        join_room(user_id, room_id)

    WS_CLIENTS.setdefault(room_id, {})
    WS_CLIENTS[room_id][user_id] = ws

    await ws.send_json({
        "type": "joined",
        "user_id": user_id,
        "room_id": room_id,
        "room": ROOMS[room_id],
        "invite_url": f"/user?invite={next((k for k,v in INVITES.items() if v['room_id']==room_id), '')}"
    })

    await broadcast_room(room_id, {
        "type": "presence",
        "message": f"{user_id} joined",
        "participants": ROOMS[room_id]["participants"]
    }, exclude_user=user_id)

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text", "")
            if not text:
                continue

            room = ROOMS[room_id]
            sender = get_user(user_id)
            delivered = []

            for target_id in room["participants"]:
                if target_id == user_id:
                    continue

                target = get_user(target_id)
                translated = krxa_translate(text, target.get("language", "auto"), room_id)

                payload = {
                    "type": "message",
                    "from": user_id,
                    "source": text,
                    "translated": translated,
                    "target_lang": target.get("language", "auto"),
                    "mode": room["mode"]
                }

                target_ws = WS_CLIENTS.get(room_id, {}).get(target_id)
                if target_ws:
                    await target_ws.send_json(payload)

                delivered.append({"to": target_id, "translated": translated})

            save_history(room_id, {
                "time": time.time(),
                "from": user_id,
                "source": text,
                "delivered": delivered
            })

            await ws.send_json({
                "type": "sent",
                "source": text,
                "delivered": delivered
            })

    except WebSocketDisconnect:
        WS_CLIENTS.get(room_id, {}).pop(user_id, None)
        log("disconnect", f"{user_id} left {room_id}")

@app.get("/user", response_class=HTMLResponse)
def user_ui(invite: str = ""):
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#071426;color:white;font-family:Arial}}
.wrap{{max-width:960px;margin:auto;padding:16px}}
.card{{background:#0b1d36;border:1px solid #18345a;border-radius:16px;padding:16px;margin:12px 0}}
button{{background:#2363ff;color:white;border:0;border-radius:12px;padding:14px 18px;margin:6px;font-weight:bold}}
input,select,textarea{{width:100%;box-sizing:border-box;background:#07182d;color:white;border:1px solid #244a78;border-radius:12px;padding:12px;margin:5px 0}}
.core{{width:140px;height:140px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:18px auto;font-size:24px;font-weight:bold;box-shadow:0 0 24px #00d084}}
.box{{background:#102a4d;padding:12px;border-radius:12px;margin:8px 0}}
.small{{color:#9fb3c8}}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h2>KRXA V50 여행/그룹 통역</h2>
    <p class="small">1기기 여행 + 2기기 통화 + 그룹 초대 통합</p>
    <div class="core">KRXA</div>

    <label>내 ID</label>
    <input id="user_id">

    <label>내 언어</label>
    <select id="language">
      <option value="auto">자동</option>
      <option value="ko">한국어</option>
      <option value="en">English</option>
      <option value="ja">日本語</option>
      <option value="zh">中文</option>
      <option value="es">Español</option>
    </select>

    <label>모드</label>
    <select id="mode">
      <option value="travel">1기기 여행</option>
      <option value="call">2기기 통역 통화</option>
      <option value="group">그룹 통역</option>
      <option value="youtube">유튜브</option>
      <option value="game">게임</option>
      <option value="field">현장</option>
    </select>

    <button onclick="createRoom()">방 만들기</button>
    <button onclick="joinInvite()">초대 입장</button>
    <button onclick="connect()">연결 시작</button>

    <p id="status">대기</p>
    <input id="invite" value="{html.escape(invite)}" placeholder="invite_id">
    <input id="room_id" placeholder="room_id">
    <input id="invite_url" placeholder="초대 주소" readonly>
  </div>

  <div class="card">
    <h3>대화</h3>
    <textarea id="text">안녕하세요. 이 근처 지하철역이 어디인가요?</textarea>
    <button onclick="send()">텍스트 전송</button>
    <button onclick="recordTranslate()">음성 통역</button>
    <div id="chat"></div>
    <audio id="ttsAudio" controls></audio>
  </div>

  <div class="card">
    <a style="color:#8ab4ff" href="/admin">ADMIN</a> |
    <a style="color:#8ab4ff" href="/api/state">STATE</a> |
    <a style="color:#8ab4ff" href="/verify">VERIFY</a>
  </div>
</div>

<script>
let ws=null;
let userId=localStorage.getItem("krxa_user_id") || ("user-"+Math.random().toString(16).slice(2,6));
document.getElementById("user_id").value=userId;

function log(t){{ document.getElementById("chat").innerHTML += "<div class='box'>"+t+"</div>"; }}
function status(t){{ document.getElementById("status").innerText=t; }}
function uid(){{ return document.getElementById("user_id").value; }}
function lang(){{ return document.getElementById("language").value; }}
function mode(){{ return document.getElementById("mode").value; }}

async function createRoom(){{
  userId=uid(); localStorage.setItem("krxa_user_id",userId);
  const fd=new FormData();
  fd.append("user_id",userId);
  fd.append("mode",mode());
  fd.append("title","KRXA "+mode());
  const r=await fetch("/api/create_room",{{method:"POST",body:fd}});
  const j=await r.json();
  document.getElementById("room_id").value=j.room_id;
  document.getElementById("invite").value=j.invite_id;
  document.getElementById("invite_url").value=location.origin+j.invite_url;
  log("방 생성: "+j.room_id+" / 초대: "+j.invite_id);
}}

async function joinInvite(){{
  const fd=new FormData();
  fd.append("user_id",uid());
  fd.append("invite_id",document.getElementById("invite").value);
  const r=await fetch("/api/join",{{method:"POST",body:fd}});
  const j=await r.json();
  if(j.ok){{
    document.getElementById("room_id").value=j.room_id;
    log("입장 완료: "+j.room_id);
  }} else {{
    log("입장 실패: "+JSON.stringify(j));
  }}
}}

function connect(){{
  userId=uid(); localStorage.setItem("krxa_user_id",userId);
  const room=document.getElementById("room_id").value;
  const invite=document.getElementById("invite").value;
  let url=(location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/room?user_id="+encodeURIComponent(userId)+"&language="+encodeURIComponent(lang())+"&mode="+encodeURIComponent(mode());
  if(room) url += "&room_id="+encodeURIComponent(room);
  if(invite) url += "&invite_id="+encodeURIComponent(invite);

  ws=new WebSocket(url);
  ws.onmessage=(ev)=>{{
    const d=JSON.parse(ev.data);
    if(d.type==="joined"){{
      document.getElementById("room_id").value=d.room_id;
      if(d.invite_url) document.getElementById("invite_url").value=location.origin+d.invite_url;
      status("연결됨: "+d.room_id);
      log("KRXA 연결됨 / 참여자: "+d.room.participants.join(", "));
    }}
    if(d.type==="presence"){{
      log("상태: "+d.message+" / "+d.participants.join(", "));
    }}
    if(d.type==="message"){{
      log("<b>"+d.from+" 원문:</b> "+d.source);
      log("<b>KRXA 통역:</b> "+d.translated);
      playTTS(d.translated);
    }}
    if(d.type==="sent"){{
      log("<b>나:</b> "+d.source);
      d.delivered.forEach(x=>log("<b>"+x.to+"에게 전달:</b> "+x.translated));
    }}
  }};
}}

function send(){{
  if(!ws || ws.readyState!==1){{ alert("먼저 연결 시작"); return; }}
  ws.send(JSON.stringify({{text:document.getElementById("text").value}}));
}}

async function playTTS(text){{
  const fd=new FormData();
  fd.append("text",text);
  const r=await fetch("/api/tts",{{method:"POST",body:fd}});
  const blob=await r.blob();
  const url=URL.createObjectURL(blob);
  const a=document.getElementById("ttsAudio");
  a.src=url; a.play();
}}

async function recordTranslate(){{
  const stream=await navigator.mediaDevices.getUserMedia({{audio:true}});
  const mr=new MediaRecorder(stream);
  let chunks=[];
  mr.ondataavailable=e=>chunks.push(e.data);
  mr.onstop=async()=>{{
    const blob=new Blob(chunks,{{type:"audio/webm"}});
    const fd=new FormData();
    fd.append("file",blob,"voice.webm");
    const sr=await fetch("/api/stt",{{method:"POST",body:fd}});
    const sj=await sr.json();
    document.getElementById("text").value=sj.text;
    send();
  }};
  mr.start();
  status("3초 녹음 중...");
  setTimeout(()=>{{mr.stop();status("녹음 완료");}},3000);
}}
</script>
</body>
</html>
"""

@app.get("/admin", response_class=HTMLResponse)
def admin():
    state = {
        "users": USERS,
        "rooms": ROOMS,
        "invites": INVITES,
        "logs": LOGS[-100:]
    }
    return f"""
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h2>KRXA V50 관제</h2>
<p><a style="color:#8ab4ff" href="/user">USER</a> | <a style="color:#8ab4ff" href="/api/state">STATE</a></p>
<pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2, default=str))}</pre>
</body></html>
"""

@app.get("/control", response_class=HTMLResponse)
def control():
    return """
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h2>KRXA V50 CONTROL</h2>
<p>V50은 user_id / invite_id / group room 기반입니다.</p>
<ul>
<li>1기기 여행: 방 생성 없이 단독 연결 가능</li>
<li>2기기 통화: 초대 링크 공유</li>
<li>그룹: 같은 invite_id로 다수 입장</li>
</ul>
<p><a style="color:#8ab4ff" href="/user">USER</a></p>
</body></html>
"""

@app.get("/verify", response_class=HTMLResponse)
def verify():
    return """
<h2>KRXA V50 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user</a></li>
<li><a href="/admin">admin</a></li>
<li><a href="/control">control</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
