import os, json, html, uuid, time, shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from openai import OpenAI

app = FastAPI(title="KRXA V59 Travel Service First")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = Path(".").resolve()
DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

SESSIONS = {}
LOGS = []

SERVICES = {
    "food": ("맛집 찾기", "🍴"),
    "map": ("길찾기", "📍"),
    "hotel": ("숙소/체크인", "🏨"),
    "taxi": ("택시/이동", "🚕"),
    "shopping": ("쇼핑/결제", "🛍"),
    "emergency": ("긴급 도움", "🚨"),
    "airport": ("공항/비행", "✈️"),
    "free": ("그냥 말하기", "🎤")
}

SYSTEM_PROMPT = """
KRXA is a travel service interface.
The visible product is travel help.
The hidden engine is natural speech-to-speech interpretation.

Rules:
- Do not say you are ChatGPT.
- Do not explain.
- Keep natural conversation flow.
- Translate naturally when languages differ.
- If same language, keep it natural.
- Help the travel situation directly.
- Output only what the user or counterpart should hear.
"""

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def log(kind, msg):
    LOGS.append({"time": now(), "kind": kind, "msg": msg})
    del LOGS[:-200]

def safe_path(p=""):
    target = (ROOT / p).resolve()
    if not str(target).startswith(str(ROOT)):
        raise ValueError("invalid path")
    return target

def history_file(session_id):
    return DATA / f"history_{session_id}.json"

def load_history(session_id):
    f = history_file(session_id)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(session_id, user_text, krxa_text, service, cards):
    h = load_history(session_id)
    h.append({
        "time": now(),
        "user": user_text,
        "krxa": krxa_text,
        "service": service,
        "cards": cards
    })
    history_file(session_id).write_text(
        json.dumps(h[-80:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def detect_service(text, service="free"):
    t = text.lower()
    if service != "free":
        return service
    if any(x in t for x in ["맛집", "식당", "restaurant", "food", "카페", "coffee"]):
        return "food"
    if any(x in t for x in ["어디", "길", "지도", "where", "direction", "station", "역"]):
        return "map"
    if any(x in t for x in ["호텔", "숙소", "체크인", "check in"]):
        return "hotel"
    if any(x in t for x in ["택시", "taxi", "uber", "이동"]):
        return "taxi"
    if any(x in t for x in ["가격", "얼마", "결제", "shopping", "shop", "price"]):
        return "shopping"
    if any(x in t for x in ["아파", "병원", "약국", "help", "emergency", "hospital"]):
        return "emergency"
    if any(x in t for x in ["공항", "비행기", "airport", "flight", "gate"]):
        return "airport"
    return "free"

def build_cards(service, text):
    q = text.replace(" ", "+")
    if service == "food":
        return [
            {"label": "주변 맛집 열기", "url": f"https://www.google.com/maps/search/restaurants+near+me+{q}"},
            {"label": "카페 찾기", "url": "https://www.google.com/maps/search/cafe+near+me"},
            {"label": "예약 문장", "text": "Can I make a reservation?"},
            {"label": "추천 질문", "text": "What do you recommend here?"}
        ]
    if service == "map":
        return [
            {"label": "지도 열기", "url": f"https://www.google.com/maps/search/{q}"},
            {"label": "가까운 역", "url": "https://www.google.com/maps/search/station+near+me"},
            {"label": "길 묻기", "text": "How can I get there?"}
        ]
    if service == "hotel":
        return [
            {"label": "체크인 문장", "text": "I would like to check in."},
            {"label": "예약 확인", "text": "I have a reservation under this name."},
            {"label": "근처 숙소", "url": "https://www.google.com/maps/search/hotel+near+me"}
        ]
    if service == "taxi":
        return [
            {"label": "목적지 보여주기", "url": f"https://www.google.com/maps/search/{q}"},
            {"label": "택시 문장", "text": "Please take me here."},
            {"label": "요금 질문", "text": "How much will it cost?"}
        ]
    if service == "shopping":
        return [
            {"label": "가격 질문", "text": "How much is this?"},
            {"label": "카드 결제", "text": "Can I pay by card?"},
            {"label": "환율 검색", "url": "https://www.google.com/search?q=exchange+rate"}
        ]
    if service == "emergency":
        return [
            {"label": "병원 찾기", "url": "https://www.google.com/maps/search/hospital+near+me"},
            {"label": "약국 찾기", "url": "https://www.google.com/maps/search/pharmacy+near+me"},
            {"label": "긴급 문장", "text": "I need help. Please call emergency services."}
        ]
    if service == "airport":
        return [
            {"label": "공항 지도", "url": "https://www.google.com/maps/search/airport+near+me"},
            {"label": "게이트 질문", "text": "Where is my boarding gate?"},
            {"label": "수하물 질문", "text": "Where can I pick up my baggage?"}
        ]
    return [
        {"label": "천천히 말하기", "text": "Please speak slowly."},
        {"label": "다시 말하기", "text": "Could you say that again?"}
    ]

def krxa_process(text, session_id, service="free"):
    history = load_history(session_id)[-12:]
    active_service = detect_service(text, service)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.append({"role": "system", "content": f"Current travel service: {active_service}"})

    for h in history:
        messages.append({"role": "user", "content": h.get("user", "")})
        messages.append({"role": "assistant", "content": h.get("krxa", "")})

    messages.append({"role": "user", "content": text})

    r = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages
    )

    result = r.choices[0].message.content or text
    cards = build_cards(active_service, text)
    save_history(session_id, text, result, active_service, cards)
    log("krxa", f"{session_id}: {active_service}")

    return {
        "source": text,
        "answer": result,
        "service": active_service,
        "cards": cards
    }

@app.get("/")
def root():
    return {"ok": True, "version": "V59", "routes": ["/user", "/app", "/control", "/dev"]}

@app.get("/health")
def health():
    return {"ok": True, "version": "V59"}

@app.get("/api/state")
def state():
    return {
        "ok": True,
        "version": "V59",
        "sessions": len(SESSIONS),
        "logs": LOGS[-50:],
        "openai_key": bool(os.getenv("OPENAI_API_KEY"))
    }

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

@app.websocket("/ws/krxa")
async def ws_krxa(ws: WebSocket):
    await ws.accept()
    session_id = ws.query_params.get("session_id") or new_id("session")
    service = ws.query_params.get("service", "free")

    SESSIONS[session_id] = {"created": now(), "service": service, "state": "LIVE"}
    await ws.send_json({"type": "init", "session_id": session_id, "service": service})

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text", "")
            service = data.get("service", service)
            if not text:
                continue
            await ws.send_json({"type": "status", "state": "THINKING"})
            result = krxa_process(text, session_id, service)
            await ws.send_json({"type": "result", "result": result})
    except WebSocketDisconnect:
        SESSIONS[session_id]["state"] = "OFF"

@app.get("/user", response_class=HTMLResponse)
def user():
    service_cards = ""
    for key, value in SERVICES.items():
        label, icon = value
        if key == "free":
            continue
        service_cards += f"""
        <div class="service" onclick="openService('{key}')">
          <div class="icon">{icon}</div>
          <div>{label}</div>
        </div>
        """

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#f7f9fc;color:#0b1220;font-family:Arial}}
.wrap{{max-width:460px;margin:auto;min-height:100vh;padding:18px;box-sizing:border-box}}
.top{{display:flex;justify-content:space-between;align-items:center}}
.logo{{font-size:26px;font-weight:800}}
.hero{{margin:18px 0;padding:22px;border-radius:26px;background:linear-gradient(135deg,#1f6bff,#12c7a4);color:white}}
.hero h1{{font-size:28px;margin:0 0 8px}}
.quick{{display:flex;gap:10px;margin-top:18px}}
.quick button{{flex:1;border:0;border-radius:18px;padding:16px;background:white;color:#1f4bd8;font-weight:bold}}
.grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:12px}}
.service{{background:white;border-radius:20px;padding:18px;text-align:center;box-shadow:0 8px 22px rgba(0,0,0,.08);cursor:pointer}}
.icon{{font-size:30px;margin-bottom:8px}}
.footer{{position:sticky;bottom:0;background:#f7f9fc;padding:12px 0;text-align:center}}
.mic{{width:78px;height:78px;border-radius:50%;border:0;background:#2363ff;color:white;font-size:34px;box-shadow:0 10px 28px rgba(35,99,255,.4)}}
.small{{font-size:13px;color:#667}}
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="logo">KRXA</div>
    <div class="small">여행 도우미</div>
  </div>

  <div class="hero">
    <h1>무엇을 도와드릴까요?</h1>
    <div>여행 서비스가 먼저, 통역은 자연스럽게 이어집니다.</div>
    <div class="quick">
      <button onclick="openService('food')">맛집</button>
      <button onclick="openService('map')">길찾기</button>
    </div>
  </div>

  <h3>여행 서비스</h3>
  <div class="grid">{service_cards}</div>

  <div class="footer">
    <button class="mic" onclick="openService('free')">🎤</button>
    <div class="small">그냥 말해도 KRXA가 알아서 도와줍니다</div>
  </div>
</div>

<script>
function openService(s){{
  window.location.href = "/app?service=" + s;
}}
</script>
</body>
</html>
"""

@app.get("/app", response_class=HTMLResponse)
def app(service: str = "free"):
    label, icon = SERVICES.get(service, SERVICES["free"])

    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{margin:0;background:#f7f9fc;color:#0b1220;font-family:Arial}}
.wrap{{max-width:460px;margin:auto;height:100vh;display:flex;flex-direction:column}}
.header{{padding:16px;background:white;border-bottom:1px solid #eee;display:flex;align-items:center;gap:12px}}
.back{{font-size:24px;cursor:pointer}}
.title{{font-size:20px;font-weight:800}}
.status{{margin-left:auto;font-size:12px;color:#00a86b}}
.chat{{flex:1;overflow:auto;padding:14px}}
.msg{{padding:14px;border-radius:18px;margin:10px 0;line-height:1.45}}
.me{{background:#dbeafe;margin-left:45px}}
.krxa{{background:white;border:1px solid #eee;margin-right:35px}}
.cards{{padding:0 14px 8px;max-height:210px;overflow:auto}}
.card{{background:white;padding:13px;border-radius:16px;margin:8px 0;box-shadow:0 5px 14px rgba(0,0,0,.06)}}
.card a{{color:#2363ff;text-decoration:none;font-weight:bold}}
.bottom{{padding:12px;background:white;border-top:1px solid #eee;text-align:center}}
.mic{{width:86px;height:86px;border-radius:50%;border:0;background:#2363ff;color:white;font-size:36px;box-shadow:0 12px 28px rgba(35,99,255,.4)}}
.tools{{display:flex;justify-content:center;gap:8px;margin-bottom:8px}}
.tools button{{border:0;border-radius:12px;padding:10px;background:#eef3ff;color:#2363ff;font-weight:bold}}
textarea{{width:100%;box-sizing:border-box;border:1px solid #ddd;border-radius:14px;padding:10px;display:none}}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    <div class="back" onclick="location.href='/user'">‹</div>
    <div class="title">{icon} {label}</div>
    <div id="status" class="status">LIVE</div>
  </div>

  <div id="chat" class="chat">
    <div class="msg krxa">어떤 도움이 필요하세요? 말하면 제가 자연스럽게 연결해드릴게요.</div>
  </div>

  <div id="cards" class="cards"></div>

  <div class="bottom">
    <div class="tools">
      <button onclick="speakerTest()">스피커</button>
      <button onclick="toggleText()">텍스트</button>
    </div>
    <textarea id="textInput" placeholder="직접 입력"></textarea>
    <button id="sendBtn" style="display:none" onclick="sendText()">전송</button>
    <br>
    <button class="mic" onclick="recordVoice()">🎤</button>
    <div style="font-size:13px;color:#667;margin-top:6px">말하면 통역과 여행 서비스가 함께 작동합니다</div>
  </div>
</div>

<script>
let sessionId = localStorage.getItem("krxa_v59_session");
if(!sessionId){{
  sessionId = "session-" + Math.random().toString(16).slice(2,10);
  localStorage.setItem("krxa_v59_session", sessionId);
}}
let service = "{service}";
let ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://") + location.host + "/ws/krxa?session_id=" + encodeURIComponent(sessionId) + "&service=" + service);

ws.onmessage = async (ev) => {{
  const d = JSON.parse(ev.data);
  if(d.type === "status") setStatus(d.state);
  if(d.type === "result"){{
    setStatus("LIVE");
    showResult(d.result);
    await playTTS(d.result.answer);
  }}
}};

function setStatus(s){{ document.getElementById("status").innerText = s; }}

function esc(s){{
  return String(s).replace(/[&<>"']/g, m => ({{"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}}[m]));
}}

function addMsg(cls, text){{
  const chat = document.getElementById("chat");
  chat.innerHTML += "<div class='msg "+cls+"'>" + esc(text) + "</div>";
  chat.scrollTop = 999999;
}}

function showResult(r){{
  addMsg("me", r.source);
  addMsg("krxa", r.answer);

  let html = "";
  r.cards.forEach(c => {{
    if(c.url) html += "<div class='card'><a target='_blank' href='"+c.url+"'>"+esc(c.label)+"</a></div>";
    else html += "<div class='card'><b>"+esc(c.label)+"</b><br>"+esc(c.text)+"</div>";
  }});
  document.getElementById("cards").innerHTML = html;
}}

function sendKRXA(text){{
  if(!ws || ws.readyState !== 1){{ alert("KRXA 연결 중입니다."); return; }}
  ws.send(JSON.stringify({{text:text, service:service}}));
}}

async function recordVoice(){{
  try{{
    setStatus("LISTENING");
    const stream = await navigator.mediaDevices.getUserMedia({{audio:true}});
    const mr = new MediaRecorder(stream);
    let chunks = [];
    mr.ondataavailable = e => chunks.push(e.data);
    mr.onstop = async () => {{
      setStatus("STT");
      const blob = new Blob(chunks, {{type:"audio/webm"}});
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");
      const r = await fetch("/api/stt", {{method:"POST", body:fd}});
      const j = await r.json();
      if(j.ok) sendKRXA(j.text);
      else alert("음성 인식 실패");
    }};
    mr.start();
    setTimeout(()=>mr.stop(), 3000);
  }}catch(e){{
    alert("마이크 권한을 허용해야 합니다.");
    setStatus("LIVE");
  }}
}}

async function playTTS(text){{
  const fd = new FormData();
  fd.append("text", text);
  const r = await fetch("/api/tts", {{method:"POST", body:fd}});
  const blob = await r.blob();
  new Audio(URL.createObjectURL(blob)).play();
}}

async function speakerTest(){{
  await playTTS("KRXA is ready to help your trip.");
}}

function toggleText(){{
  const t = document.getElementById("textInput");
  const b = document.getElementById("sendBtn");
  const show = t.style.display === "none" || t.style.display === "";
  t.style.display = show ? "block" : "none";
  b.style.display = show ? "inline-block" : "none";
}}

function sendText(){{
  const t = document.getElementById("textInput").value.trim();
  if(t) sendKRXA(t);
}}
</script>
</body>
</html>
"""

@app.get("/control", response_class=HTMLResponse)
def control():
    state = {
        "version": "V59",
        "sessions": SESSIONS,
        "logs": LOGS[-100:],
        "openai_key": bool(os.getenv("OPENAI_API_KEY"))
    }
    return f"""
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h1>KRXA V59 CONTROL</h1>
<p><a style="color:#8ab4ff" href="/user">USER</a> | <a style="color:#8ab4ff" href="/dev">DEV</a> | <a style="color:#8ab4ff" href="/api/state">STATE</a></p>
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
<h2>KRXA DEV FILE EDIT</h2>
<p>{html.escape(path)}</p>
<form method="post" action="/dev/save">
<input type="hidden" name="path" value="{html.escape(path)}">
<textarea name="content" style="width:100%;height:70vh;">{content}</textarea>
<br><button type="submit">SAVE</button>
</form>
<form method="post" action="/dev/delete">
<input type="hidden" name="path" value="{html.escape(path)}">
<button type="submit">DELETE</button>
</form>
<p><a href="/dev">FILE LIST</a> | <a href="/control">CONTROL</a></p>
</body></html>
"""

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")

    return f"""
<html><body style="font-family:Arial;padding:20px">
<h2>KRXA DEV</h2>
<p><a href="/user">USER</a> | <a href="/control">CONTROL</a></p>
<form method="post" action="/dev/create">
<input name="path" placeholder="new_file.py or folder/file.txt">
<button type="submit">CREATE</button>
</form>
<ul>{''.join(items)}</ul>
</body></html>
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
<h2>KRXA V59 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user</a></li>
<li><a href="/app?service=food">food service</a></li>
<li><a href="/control">control</a></li>
<li><a href="/dev">dev</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
