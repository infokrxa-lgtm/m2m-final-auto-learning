import os, json, html, uuid, time, shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from openai import OpenAI

app = FastAPI(title="KRXA V51 Product UI")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = Path(".").resolve()
DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

USERS, ROOMS, INVITES, WS_CLIENTS, LOGS = {}, {}, {}, {}, []

MODES = {
    "travel": "여행",
    "call": "통화",
    "group": "그룹",
    "youtube": "유튜브",
    "game": "게임",
    "field": "현장"
}

def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def log(kind, msg):
    LOGS.append({"time": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})
    del LOGS[:-300]

def safe_path(p=""):
    target = (ROOT / p).resolve()
    if not str(target).startswith(str(ROOT)):
        raise ValueError("invalid path")
    return target

def history_file(room_id):
    return DATA / f"history_{room_id}.json"

def load_history(room_id):
    f = history_file(room_id)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(room_id, item):
    h = load_history(room_id)
    h.append(item)
    history_file(room_id).write_text(
        json.dumps(h[-300:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def get_user(user_id, language="auto"):
    if user_id not in USERS:
        USERS[user_id] = {
            "user_id": user_id,
            "device_id": new_id("device"),
            "language": language,
            "created": time.time(),
            "last_seen": time.time()
        }
    USERS[user_id]["last_seen"] = time.time()
    USERS[user_id]["language"] = language or USERS[user_id].get("language", "auto")
    return USERS[user_id]

def create_room(owner_id, mode="travel"):
    room_id = new_id("room")
    invite_id = new_id("invite")
    ROOMS[room_id] = {
        "room_id": room_id,
        "owner_id": owner_id,
        "mode": mode,
        "participants": [owner_id],
        "state": "LIVE",
        "created": time.time()
    }
    INVITES[invite_id] = {"invite_id": invite_id, "room_id": room_id, "created": time.time()}
    log("room", f"{room_id} created mode={mode}")
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
- UI shows only KRXA.
- You are not a conversation participant.
- If same language, relay naturally.
- If different language, translate naturally for the target user.
- Return only final output.
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
    for uid, ws in list(WS_CLIENTS.get(room_id, {}).items()):
        if uid == exclude:
            continue
        try:
            await ws.send_json(payload)
        except Exception:
            pass

@app.get("/")
def home():
    return {"ok": True, "version": "V51", "routes": ["/user", "/app", "/control", "/admin"]}

@app.get("/health")
def health():
    return {"ok": True, "version": "V51"}

@app.get("/api/state")
def api_state():
    return {
        "ok": True,
        "version": "V51",
        "users": len(USERS),
        "rooms": ROOMS,
        "invites": INVITES,
        "logs": LOGS[-80:],
        "modes": MODES
    }

@app.post("/api/create_room")
def api_create_room(user_id: str = Form(...), mode: str = Form("travel")):
    get_user(user_id)
    room_id, invite_id = create_room(user_id, mode)
    return {
        "ok": True,
        "room_id": room_id,
        "invite_id": invite_id,
        "invite_url": f"/app?invite={invite_id}&mode={mode}"
    }

@app.post("/api/join")
def api_join(user_id: str = Form(...), room_id: str = Form(""), invite_id: str = Form(""), language: str = Form("auto")):
    get_user(user_id, language)
    if invite_id:
        inv = INVITES.get(invite_id)
        if not inv:
            return {"ok": False, "error": "invalid invite"}
        room_id = inv["room_id"]
    if not room_id:
        return {"ok": False, "error": "missing room_id"}
    return {"ok": join_room(user_id, room_id), "room_id": room_id, "room": ROOMS.get(room_id)}

@app.post("/api/send")
def api_send(user_id: str = Form(...), room_id: str = Form(...), text: str = Form(...)):
    if room_id not in ROOMS:
        return {"ok": False, "error": "invalid room"}

    outputs = []
    for target_id in ROOMS[room_id]["participants"]:
        if target_id == user_id:
            continue
        target = get_user(target_id)
        out = krxa_translate(text, target.get("language", "auto"), room_id)
        outputs.append({"to": target_id, "translated": out})

    save_history(room_id, {"time": time.time(), "from": user_id, "source": text, "outputs": outputs})
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
    audio = client.audio.speech.create(model=TTS_MODEL, voice="alloy", input=text)
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.websocket("/ws/room")
async def ws_room(ws: WebSocket):
    await ws.accept()

    user_id = ws.query_params.get("user_id") or new_id("user")
    language = ws.query_params.get("language", "auto")
    mode = ws.query_params.get("mode", "travel")
    room_id = ws.query_params.get("room_id")
    invite_id = ws.query_params.get("invite_id")

    get_user(user_id, language)

    if invite_id and not room_id:
        inv = INVITES.get(invite_id)
        if inv:
            room_id = inv["room_id"]

    if not room_id:
        room_id, invite_id = create_room(user_id, mode)
    else:
        join_room(user_id, room_id)

    WS_CLIENTS.setdefault(room_id, {})[user_id] = ws

    await ws.send_json({
        "type": "joined",
        "user_id": user_id,
        "room_id": room_id,
        "room": ROOMS[room_id],
        "invite_url": f"/app?invite={next((k for k,v in INVITES.items() if v['room_id']==room_id), '')}&mode={mode}"
    })

    await broadcast(room_id, {
        "type": "presence",
        "participants": ROOMS[room_id]["participants"]
    }, exclude=user_id)

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text", "")
            if not text:
                continue

            delivered = []
            for target_id in ROOMS[room_id]["participants"]:
                if target_id == user_id:
                    continue

                target = get_user(target_id)
                translated = krxa_translate(text, target.get("language", "auto"), room_id)

                payload = {
                    "type": "message",
                    "from": user_id,
                    "source": text,
                    "translated": translated,
                    "mode": mode
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

            await ws.send_json({"type": "sent", "source": text, "delivered": delivered})

    except WebSocketDisconnect:
        WS_CLIENTS.get(room_id, {}).pop(user_id, None)
        log("disconnect", f"{user_id} left {room_id}")

@app.get("/user", response_class=HTMLResponse)
def user_home():
    cards = "".join([
        f"""<div class="card mode" onclick="openMode('{k}')"><h3>{v}</h3><p>KRXA {v} 실행</p></div>"""
        for k, v in MODES.items()
    ])
    return f"""
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#071426;color:white;font-family:Arial}}
.wrap{{max-width:980px;margin:auto;padding:20px}}
.hero{{text-align:center;background:#0b1d36;border:1px solid #18345a;border-radius:22px;padding:26px;margin-bottom:18px}}
.core{{width:140px;height:140px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:20px auto;font-size:26px;font-weight:bold;box-shadow:0 0 24px #00d084}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:14px}}
.card{{background:#0b1d36;border:1px solid #18345a;border-radius:18px;padding:20px;cursor:pointer}}
.card:hover{{background:#102a4d}}
@media(max-width:700px){{.grid{{grid-template-columns:1fr}}}}
</style></head>
<body><div class="wrap">
<div class="hero">
<h1>KRXA 말대말</h1>
<p>핸드폰 한 대부터 그룹 통역까지</p>
<div class="core">KRXA</div>
</div>
<div class="grid">{cards}</div>
</div>
<script>
function openMode(m){{ window.open('/app?mode='+m, '_blank'); }}
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
.wrap{{max-width:900px;margin:auto;padding:16px}}
.card{{background:#0b1d36;border:1px solid #18345a;border-radius:16px;padding:16px;margin:12px 0}}
button{{background:#2363ff;color:white;border:0;border-radius:12px;padding:13px 16px;margin:5px;font-weight:bold}}
input,select,textarea{{width:100%;box-sizing:border-box;background:#07182d;color:white;border:1px solid #244a78;border-radius:12px;padding:12px;margin:5px 0}}
.core{{width:130px;height:130px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:18px auto;font-size:24px;font-weight:bold;box-shadow:0 0 24px #00d084}}
.box{{background:#102a4d;padding:12px;border-radius:12px;margin:8px 0}}
</style></head>
<body><div class="wrap">
<div class="card">
<h2>KRXA {mode_label}</h2>
<div class="core">KRXA</div>
<label>내 ID</label><input id="user_id">
<label>내 언어</label>
<select id="language">
<option value="auto">자동</option><option value="ko">한국어</option><option value="en">English</option>
<option value="ja">日本語</option><option value="zh">中文</option><option value="es">Español</option>
</select>
<button onclick="createRoom()">초대 만들기</button>
<button onclick="joinInvite()">초대 입장</button>
<button onclick="connect()">연결 시작</button>
<input id="invite" value="{html.escape(invite)}" placeholder="invite_id">
<input id="room_id" placeholder="room_id">
<input id="invite_url" placeholder="초대 주소" readonly>
<p id="status">대기</p>
</div>

<div class="card">
<h3>대화</h3>
<textarea id="text">안녕하세요. 이 근처 지하철역이 어디인가요?</textarea>
<button onclick="send()">텍스트 전송</button>
<button onclick="recordTranslate()">음성 통역</button>
<div id="chat"></div>
<audio id="ttsAudio" controls></audio>
</div>
</div>

<script>
let ws=null;
let userId=localStorage.getItem("krxa_user_id") || ("user-"+Math.random().toString(16).slice(2,6));
document.getElementById("user_id").value=userId;
function log(t){{document.getElementById("chat").innerHTML+="<div class='box'>"+t+"</div>";}}
function status(t){{document.getElementById("status").innerText=t;}}
function uid(){{return document.getElementById("user_id").value;}}
function lang(){{return document.getElementById("language").value;}}

async function createRoom(){{
 userId=uid(); localStorage.setItem("krxa_user_id",userId);
 const fd=new FormData(); fd.append("user_id",userId); fd.append("mode","{mode}");
 const r=await fetch("/api/create_room",{{method:"POST",body:fd}});
 const j=await r.json();
 document.getElementById("room_id").value=j.room_id;
 document.getElementById("invite").value=j.invite_id;
 document.getElementById("invite_url").value=location.origin+j.invite_url;
 log("초대 생성: "+location.origin+j.invite_url);
}}

async function joinInvite(){{
 const fd=new FormData(); fd.append("user_id",uid()); fd.append("invite_id",document.getElementById("invite").value); fd.append("language",lang());
 const r=await fetch("/api/join",{{method:"POST",body:fd}});
 const j=await r.json();
 if(j.ok){{document.getElementById("room_id").value=j.room_id;log("입장 완료: "+j.room_id);}}
 else log("입장 실패: "+JSON.stringify(j));
}}

function connect(){{
 const room=document.getElementById("room_id").value;
 const invite=document.getElementById("invite").value;
 let url=(location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/room?user_id="+encodeURIComponent(uid())+"&language="+encodeURIComponent(lang())+"&mode={mode}";
 if(room) url+="&room_id="+encodeURIComponent(room);
 if(invite) url+="&invite_id="+encodeURIComponent(invite);
 ws=new WebSocket(url);
 ws.onmessage=(ev)=>{{
  const d=JSON.parse(ev.data);
  if(d.type==="joined"){{document.getElementById("room_id").value=d.room_id;if(d.invite_url)document.getElementById("invite_url").value=location.origin+d.invite_url;status("연결됨: "+d.room_id);log("KRXA 연결됨 / 참여자: "+d.room.participants.join(", "));}}
  if(d.type==="presence")log("참여자: "+d.participants.join(", "));
  if(d.type==="message"){{log("<b>"+d.from+" 원문:</b> "+d.source);log("<b>KRXA 통역:</b> "+d.translated);playTTS(d.translated);}}
  if(d.type==="sent"){{log("<b>나:</b> "+d.source);d.delivered.forEach(x=>log("<b>"+x.to+" 전달:</b> "+x.translated));}}
 }};
}}

function send(){{
 if(!ws || ws.readyState!==1){{alert("먼저 연결 시작");return;}}
 ws.send(JSON.stringify({{text:document.getElementById("text").value}}));
}}

async function playTTS(text){{
 const fd=new FormData(); fd.append("text",text);
 const r=await fetch("/api/tts",{{method:"POST",body:fd}});
 const blob=await r.blob(); const url=URL.createObjectURL(blob);
 const a=document.getElementById("ttsAudio"); a.src=url; a.play();
}}

async function recordTranslate(){{
 const stream=await navigator.mediaDevices.getUserMedia({{audio:true}});
 const mr=new MediaRecorder(stream); let chunks=[];
 mr.ondataavailable=e=>chunks.push(e.data);
 mr.onstop=async()=>{{
  const blob=new Blob(chunks,{{type:"audio/webm"}});
  const fd=new FormData(); fd.append("file",blob,"voice.webm");
  const sr=await fetch("/api/stt",{{method:"POST",body:fd}});
  const sj=await sr.json(); document.getElementById("text").value=sj.text; send();
 }};
 mr.start(); status("3초 녹음 중..."); setTimeout(()=>{{mr.stop();status("녹음 완료");}},3000);
}}
</script></body></html>
"""

@app.get("/control", response_class=HTMLResponse)
def control():
    state = {"users": USERS, "rooms": ROOMS, "invites": INVITES, "logs": LOGS[-120:]}
    return f"""
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h1>KRXA V51 CONTROL</h1>
<p><a style="color:#8ab4ff" href="/user">USER</a> | <a style="color:#8ab4ff" href="/admin">ADMIN/DEV</a></p>
<h2>실행 컨트롤</h2>
<button onclick="location.href='/app?mode=travel'">여행 실행</button>
<button onclick="location.href='/app?mode=call'">통화 실행</button>
<button onclick="location.href='/app?mode=group'">그룹 실행</button>
<button onclick="location.href='/app?mode=youtube'">유튜브 실행</button>
<button onclick="location.href='/app?mode=game'">게임 실행</button>
<button onclick="location.href='/app?mode=field'">현장 실행</button>
<h2>전체 상태</h2>
<pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2, default=str))}</pre>
</body></html>
"""

@app.get("/admin", response_class=HTMLResponse)
def admin(path: str = ""):
    root = safe_path(path)
    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        return f"""
<html><body style="font-family:Arial;padding:20px">
<h2>KRXA DEV EDIT</h2>
<p>{html.escape(path)}</p>
<form method="post" action="/admin/save">
<input type="hidden" name="path" value="{html.escape(path)}">
<textarea name="content" style="width:100%;height:70vh;">{content}</textarea>
<br><button type="submit">SAVE</button>
</form>
<form method="post" action="/admin/delete">
<input type="hidden" name="path" value="{html.escape(path)}">
<button type="submit">DELETE</button>
</form>
<p><a href="/admin">FILE LIST</a> | <a href="/control">CONTROL</a></p>
</body></html>
"""

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/admin?path={label}'>{icon} {label}</a></li>")

    return f"""
<html><body style="font-family:Arial;padding:20px">
<h2>KRXA ADMIN / DEV</h2>
<p><a href="/user">USER</a> | <a href="/control">CONTROL</a> | <a href="/api/state">STATE</a></p>
<h3>파일 생성</h3>
<form method="post" action="/admin/create">
<input name="path" placeholder="new_file.py or folder/file.txt">
<button type="submit">CREATE</button>
</form>
<ul>{''.join(items)}</ul>
</body></html>
"""

@app.post("/admin/save")
def admin_save(path: str = Form(...), content: str = Form(...)):
    safe_path(path).write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/admin?path={path}", status_code=303)

@app.post("/admin/create")
def admin_create(path: str = Form(...)):
    target = safe_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        target.write_text("", encoding="utf-8")
    return RedirectResponse(url=f"/admin?path={path}", status_code=303)

@app.post("/admin/delete")
def admin_delete(path: str = Form(...)):
    target = safe_path(path)
    if target.is_file():
        target.unlink()
    elif target.is_dir():
        shutil.rmtree(target)
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/dev")
def dev_redirect():
    return RedirectResponse("/admin", status_code=302)

@app.get("/verify", response_class=HTMLResponse)
def verify():
    return """
<h2>KRXA V51 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user</a></li>
<li><a href="/control">control</a></li>
<li><a href="/admin">admin/dev</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
