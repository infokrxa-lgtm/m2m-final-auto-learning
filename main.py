import os, json, html, uuid, time, shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from openai import OpenAI

app = FastAPI(title="KRXA V58 Natural Travel Service")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = Path(".").resolve()
DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

SESSIONS = {}
LOGS = []

INVITE_PROMPT = """
[KRXA V58]

역할:
- KRXA는 자연대화 기반 여행 서비스이다.
- 통역은 기본 기능이다.
- 여행 중 필요한 서비스를 자연스럽게 제공한다.
- 내부 AI 엔진은 사용자에게 노출되지 않는다.

규칙:
1. 대화 흐름을 유지한다.
2. 이전 history를 반영한다.
3. 입력 언어를 자동 감지한다.
4. 같은 언어면 자연스럽게 유지한다.
5. 다른 언어면 상대가 이해할 수 있게 자연스럽게 통역한다.
6. 설명하지 말고 사용자에게 바로 보여줄 말만 출력한다.
7. 여행 상황이면 필요한 행동을 짧게 돕는다.
"""

def new_id(prefix):
    return f"{prefix}-{uuid.uuid4().hex[:8]}"

def now():
    return time.strftime("%Y-%m-%d %H:%M:%S")

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

def save_history(session_id, user_text, krxa_text, intent, cards):
    h = load_history(session_id)
    h.append({
        "time": now(),
        "user": user_text,
        "krxa": krxa_text,
        "intent": intent,
        "cards": cards
    })
    history_file(session_id).write_text(
        json.dumps(h[-80:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def analyze_intent(text):
    t = text.lower()

    if any(x in t for x in ["맛집", "식당", "restaurant", "food", "eat", "밥", "카페", "coffee"]):
        return "food"
    if any(x in t for x in ["어디", "길", "지도", "where", "direction", "station", "역", "택시"]):
        return "map"
    if any(x in t for x in ["가격", "얼마", "price", "cost", "money", "환율", "exchange"]):
        return "price"
    if any(x in t for x in ["아파", "병원", "약국", "help", "emergency", "hospital", "pharmacy"]):
        return "emergency"
    if any(x in t for x in ["예약", "reservation", "book", "booking"]):
        return "reservation"
    if any(x in t for x in ["호텔", "숙소", "check in", "체크인"]):
        return "hotel"
    if any(x in t for x in ["공항", "airport", "flight", "비행기", "게이트"]):
        return "airport"
    if any(x in t for x in ["쇼핑", "shopping", "선물", "souvenir", "면세"]):
        return "shopping"

    return "general"

def build_cards(intent, text):
    q = text.replace(" ", "+")
    cards = []

    if intent == "food":
        cards = [
            {"label": "🍴 맛집 찾기", "url": f"https://www.google.com/maps/search/restaurants+near+me+{q}"},
            {"label": "☕ 카페 찾기", "url": "https://www.google.com/maps/search/cafe+near+me"},
            {"label": "📞 예약 문장", "text": "Can I make a reservation?"},
            {"label": "👍 추천 질문", "text": "What do you recommend here?"}
        ]

    elif intent == "map":
        cards = [
            {"label": "📍 지도 열기", "url": f"https://www.google.com/maps/search/{q}"},
            {"label": "🚇 가까운 역 찾기", "url": "https://www.google.com/maps/search/subway+station+near+me"},
            {"label": "🚕 택시 문장", "text": "Please take me here."},
            {"label": "🧭 길 묻기", "text": "How can I get there?"}
        ]

    elif intent == "price":
        cards = [
            {"label": "💳 가격 질문", "text": "How much is this?"},
            {"label": "💳 카드 결제", "text": "Can I pay by card?"},
            {"label": "💱 환율 검색", "url": "https://www.google.com/search?q=exchange+rate"}
        ]

    elif intent == "emergency":
        cards = [
            {"label": "🚨 병원 찾기", "url": "https://www.google.com/maps/search/hospital+near+me"},
            {"label": "💊 약국 찾기", "url": "https://www.google.com/maps/search/pharmacy+near+me"},
            {"label": "🆘 긴급 문장", "text": "I need help. Please call emergency services."}
        ]

    elif intent == "reservation":
        cards = [
            {"label": "📞 예약 문장", "text": "I would like to make a reservation."},
            {"label": "⏰ 시간 확인", "text": "What time is available?"},
            {"label": "👥 인원 말하기", "text": "A table for two, please."}
        ]

    elif intent == "hotel":
        cards = [
            {"label": "🏨 체크인 문장", "text": "I would like to check in."},
            {"label": "📄 예약 확인", "text": "I have a reservation under this name."},
            {"label": "📍 호텔 주변", "url": "https://www.google.com/maps/search/hotel+near+me"}
        ]

    elif intent == "airport":
        cards = [
            {"label": "✈️ 공항 지도", "url": "https://www.google.com/maps/search/airport+near+me"},
            {"label": "🛂 게이트 질문", "text": "Where is my boarding gate?"},
            {"label": "🧳 수하물 질문", "text": "Where can I pick up my baggage?"}
        ]

    elif intent == "shopping":
        cards = [
            {"label": "🛍 쇼핑 장소", "url": "https://www.google.com/maps/search/shopping+near+me"},
            {"label": "🎁 선물 추천", "text": "What is a popular local gift?"},
            {"label": "💳 결제 질문", "text": "Can I pay by card?"}
        ]

    else:
        cards = [
            {"label": "🔁 다시 말하기", "text": "Could you say that again, please?"},
            {"label": "🐢 천천히 말하기", "text": "Please speak slowly."}
        ]

    return cards

def krxa_process(text, session_id):
    history = load_history(session_id)[-12:]

    messages = [{"role": "system", "content": INVITE_PROMPT}]

    for h in history:
        messages.append({"role": "user", "content": h.get("user", "")})
        messages.append({"role": "assistant", "content": h.get("krxa", "")})

    messages.append({"role": "user", "content": text})

    r = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=messages
    )

    result = r.choices[0].message.content or text
    intent = analyze_intent(text)
    cards = build_cards(intent, text)

    save_history(session_id, text, result, intent, cards)
    log("krxa", f"{session_id}: {intent}")

    return {
        "text": text,
        "translated": result,
        "intent": intent,
        "cards": cards
    }

@app.get("/")
def root():
    return {"ok": True, "version": "V58", "routes": ["/user", "/control", "/dev", "/health"]}

@app.get("/health")
def health():
    return {"ok": True, "version": "V58-NATURAL-TRAVEL"}

@app.get("/api/state")
def api_state():
    return {
        "ok": True,
        "version": "V58",
        "sessions": len(SESSIONS),
        "logs": LOGS[-50:],
        "storage": str(DATA),
        "openai_key": bool(os.getenv("OPENAI_API_KEY"))
    }

@app.get("/history")
def history(session_id: str = "default"):
    return {"ok": True, "session_id": session_id, "history": load_history(session_id)}

@app.post("/api/text")
def api_text(text: str = Form(...), session_id: str = Form("default")):
    return {"ok": True, "result": krxa_process(text, session_id)}

@app.post("/api/stt")
async def stt(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            tr = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=f
            )
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
    SESSIONS[session_id] = {"created": now(), "state": "LIVE"}

    await ws.send_json({"type": "init", "session_id": session_id, "state": "LIVE"})

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text", "")
            if not text:
                continue

            await ws.send_json({"type": "status", "state": "THINKING"})
            result = krxa_process(text, session_id)
            await ws.send_json({"type": "result", "result": result, "state": "LIVE"})

    except WebSocketDisconnect:
        SESSIONS[session_id]["state"] = "OFF"
        log("disconnect", session_id)

@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#071426;color:white;font-family:Arial}
.wrap{max-width:460px;margin:auto;height:100vh;display:flex;flex-direction:column;box-sizing:border-box}
.header{padding:12px;text-align:center;font-size:18px;font-weight:bold}
.sub{font-size:13px;color:#9fb3c8;margin-top:4px}
.chat{flex:1;overflow:auto;padding:12px}
.msg{margin:10px 0;padding:12px;border-radius:14px;line-height:1.45}
.me{background:#163b65}
.krxa{background:#0b1d36;border:1px solid #18345a}
.micbar{text-align:center;padding:12px;border-top:1px solid #18345a}
.mic{width:88px;height:88px;border-radius:50%;background:#2363ff;display:flex;align-items:center;justify-content:center;font-size:36px;margin:auto;cursor:pointer;box-shadow:0 0 22px #2363ff}
.cards{padding:8px 12px;max-height:190px;overflow:auto}
.card{background:#102a4d;padding:10px;margin:6px 0;border-radius:12px;font-size:14px}
a{color:#9fd3ff;text-decoration:none}
.status{font-size:13px;color:#00d084;margin-top:6px}
.hiddenInput{width:100%;box-sizing:border-box;background:#07182d;color:white;border:1px solid #244a78;border-radius:12px;padding:10px;margin-top:8px}
.row{display:flex;gap:6px;justify-content:center;flex-wrap:wrap}
.smallbtn{font-size:12px;padding:8px 10px;border:0;border-radius:10px;background:#1c4ed8;color:white}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">
    KRXA 여행 도우미
    <div class="sub">자연대화 통역 + 여행 서비스</div>
    <div id="status" class="status">LIVE</div>
  </div>

  <div id="chat" class="chat"></div>

  <div id="cards" class="cards"></div>

  <div class="micbar">
    <div class="row">
      <button class="smallbtn" onclick="speakerTest()">스피커 테스트</button>
      <button class="smallbtn" onclick="toggleText()">텍스트 입력</button>
    </div>
    <textarea id="textInput" class="hiddenInput" style="display:none" placeholder="직접 입력"></textarea>
    <button id="sendTextBtn" class="smallbtn" style="display:none" onclick="sendText()">전송</button>
    <div class="mic" onclick="startTalk()">🎤</div>
    <div class="sub">말하면 KRXA가 통역하고 여행 서비스를 제안합니다.</div>
  </div>
</div>

<script>
let sessionId = localStorage.getItem("krxa_v58_session");
if(!sessionId){
  sessionId = "session-" + Math.random().toString(16).slice(2,10);
  localStorage.setItem("krxa_v58_session", sessionId);
}

let ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://") + location.host + "/ws/krxa?session_id=" + encodeURIComponent(sessionId));

ws.onmessage = async (ev) => {
  const d = JSON.parse(ev.data);

  if(d.type === "init"){
    setStatus("LIVE");
    addMsg("krxa", "KRXA가 준비되었습니다. 마이크를 누르고 자연스럽게 말하세요.");
  }

  if(d.type === "status"){
    setStatus(d.state);
  }

  if(d.type === "result"){
    setStatus("LIVE");
    showResult(d.result);
    await playTTS(d.result.translated);
  }
};

function setStatus(s){
  document.getElementById("status").innerText = s;
}

function addMsg(type, text){
  const cls = type === "me" ? "me" : "krxa";
  document.getElementById("chat").innerHTML += "<div class='msg "+cls+"'>"+escapeHtml(text)+"</div>";
  document.getElementById("chat").scrollTop = 999999;
}

function escapeHtml(s){
  return String(s).replace(/[&<>"']/g, function(m){
    return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#039;"}[m];
  });
}

function showResult(r){
  addMsg("me", r.text);
  addMsg("krxa", r.translated);

  let html = "";
  r.cards.forEach(c=>{
    if(c.url){
      html += "<div class='card'><a target='_blank' href='"+c.url+"'>"+escapeHtml(c.label)+"</a></div>";
    } else if(c.text){
      html += "<div class='card'><b>"+escapeHtml(c.label)+"</b><br>"+escapeHtml(c.text)+"</div>";
    }
  });
  document.getElementById("cards").innerHTML = html;
}

function sendToKRXA(text){
  if(!ws || ws.readyState !== 1){
    alert("KRXA 연결 중입니다. 잠시 후 다시 시도하세요.");
    return;
  }
  ws.send(JSON.stringify({text:text}));
}

async function startTalk(){
  try{
    setStatus("LISTENING");
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    const mr = new MediaRecorder(stream);
    let chunks = [];

    mr.ondataavailable = e => chunks.push(e.data);

    mr.onstop = async () => {
      setStatus("STT");
      const blob = new Blob(chunks, {type:"audio/webm"});
      const fd = new FormData();
      fd.append("file", blob, "voice.webm");

      const sr = await fetch("/api/stt", {method:"POST", body:fd});
      const sj = await sr.json();

      if(!sj.ok){
        alert("음성 인식 실패");
        setStatus("LIVE");
        return;
      }

      sendToKRXA(sj.text);
    };

    mr.start();
    setTimeout(()=>mr.stop(), 3000);
  }catch(e){
    alert("마이크 권한을 허용해야 합니다.");
    setStatus("LIVE");
  }
}

async function playTTS(text){
  const fd = new FormData();
  fd.append("text", text);
  const r = await fetch("/api/tts", {method:"POST", body:fd});
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.play();
}

async function speakerTest(){
  await playTTS("KRXA speaker test is working.");
}

function toggleText(){
  const t = document.getElementById("textInput");
  const b = document.getElementById("sendTextBtn");
  const show = t.style.display === "none";
  t.style.display = show ? "block" : "none";
  b.style.display = show ? "inline-block" : "none";
}

function sendText(){
  const t = document.getElementById("textInput").value;
  if(t.trim()){
    sendToKRXA(t.trim());
  }
}
</script>
</body>
</html>
"""

@app.get("/control", response_class=HTMLResponse)
def control():
    state = {
        "version": "V58",
        "sessions": SESSIONS,
        "logs": LOGS[-100:],
        "openai_key": bool(os.getenv("OPENAI_API_KEY"))
    }
    return f"""
<html>
<body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h1>KRXA V58 CONTROL</h1>
<p><a style="color:#8ab4ff" href="/user">USER</a> | <a style="color:#8ab4ff" href="/dev">DEV</a> | <a style="color:#8ab4ff" href="/api/state">STATE</a></p>
<h2>서비스 상태</h2>
<pre>{html.escape(json.dumps(state, ensure_ascii=False, indent=2, default=str))}</pre>
</body>
</html>
"""

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)

    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        return f"""
<html>
<body style="font-family:Arial;padding:20px">
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
</body>
</html>
"""

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")

    return f"""
<html>
<body style="font-family:Arial;padding:20px">
<h2>KRXA DEV</h2>
<p><a href="/user">USER</a> | <a href="/control">CONTROL</a></p>
<form method="post" action="/dev/create">
<input name="path" placeholder="new_file.py or folder/file.txt">
<button type="submit">CREATE</button>
</form>
<ul>{''.join(items)}</ul>
</body>
</html>
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
<h2>KRXA V58 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user</a></li>
<li><a href="/control">control</a></li>
<li><a href="/dev">dev</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
