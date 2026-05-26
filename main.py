import os, json, uuid, time, html
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Form
from fastapi.responses import HTMLResponse, Response
from openai import OpenAI

app = FastAPI(title="KRXA V49 WebRTC + Translate")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

ROOMS = {}
SIGNAL_WS = {}
LOGS = []


def log(kind, msg):
    LOGS.append({"time": time.strftime("%H:%M:%S"), "kind": kind, "msg": msg})
    del LOGS[:-100]


def hfile(room_id):
    return DATA / f"history_{room_id}.json"


def load_history(room_id):
    f = hfile(room_id)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(room_id, user, out):
    h = load_history(room_id)
    h.append({"user": user, "out": out, "time": time.time()})
    hfile(room_id).write_text(json.dumps(h[-100:], ensure_ascii=False, indent=2), encoding="utf-8")


def translate_text(text, room_id="default"):
    history = load_history(room_id)[-10:]
    prompt = f"""
KRXA 내부 통역 엔진.

규칙:
- UI에는 KRXA만 보인다.
- 너는 내부 통역만 수행한다.
- 같은 언어면 자연스럽게 유지한다.
- 다른 언어면 상대가 이해할 언어로 번역한다.
- 설명하지 말고 결과만 반환한다.
- 짧고 현장 대화처럼 출력한다.

history:
{json.dumps(history, ensure_ascii=False)}

입력:
{text}
"""
    r = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
    )
    out = r.choices[0].message.content or text
    save_history(room_id, text, out)
    return out


@app.get("/")
def home():
    return {"ok": True, "version": "V49-WebRTC-KRXA"}


@app.get("/health")
def health():
    return {"ok": True, "version": "V49-WebRTC-KRXA"}


@app.get("/api/state")
def state():
    return {
        "ok": True,
        "version": "V49",
        "rooms": list(ROOMS.keys()),
        "room_count": len(ROOMS),
        "logs": LOGS[-30:],
        "krxa": {
            "core": "LIVE",
            "webrtc_signaling": "ON",
            "stt": "ON",
            "translate": "ON",
            "tts": "ON",
        },
    }


@app.get("/history")
def history(room_id: str = "default"):
    return {"ok": True, "room_id": room_id, "history": load_history(room_id)}


@app.post("/api/translate")
def api_translate(text: str = Form(...), room_id: str = Form("default")):
    return {"ok": True, "translated": translate_text(text, room_id)}


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
        input=text,
    )
    return Response(content=audio.read(), media_type="audio/mpeg")


@app.websocket("/ws/signal")
async def signal(ws: WebSocket):
    await ws.accept()
    room_id = ws.query_params.get("room", "demo")
    user_id = ws.query_params.get("user", "user-" + uuid.uuid4().hex[:4])

    ROOMS.setdefault(room_id, {"users": [], "created": time.time()})
    if user_id not in ROOMS[room_id]["users"]:
        ROOMS[room_id]["users"].append(user_id)

    SIGNAL_WS.setdefault(room_id, {})
    SIGNAL_WS[room_id][user_id] = ws

    await ws.send_json({"type": "joined", "room": room_id, "user": user_id})
    log("join", f"{user_id} joined {room_id}")

    try:
        while True:
            data = await ws.receive_json()
            target = data.get("target")
            payload = data.get("payload")
            event_type = data.get("type")

            peers = SIGNAL_WS.get(room_id, {})
            if target and target in peers:
                await peers[target].send_json({
                    "type": event_type,
                    "from": user_id,
                    "payload": payload,
                })
            else:
                for uid, peer in peers.items():
                    if uid != user_id:
                        await peer.send_json({
                            "type": event_type,
                            "from": user_id,
                            "payload": payload,
                        })

    except WebSocketDisconnect:
        SIGNAL_WS.get(room_id, {}).pop(user_id, None)
        log("leave", f"{user_id} left {room_id}")


@app.get("/call", response_class=HTMLResponse)
@app.get("/user", response_class=HTMLResponse)
def call_ui():
    return """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;background:#071426;color:white;font-family:Arial}
.wrap{max-width:900px;margin:auto;padding:16px}
.card{background:#0b1d36;border:1px solid #18345a;border-radius:16px;padding:16px;margin:12px 0}
button{background:#2363ff;color:white;border:0;border-radius:12px;padding:14px 18px;margin:6px;font-weight:bold}
input,textarea{width:100%;box-sizing:border-box;background:#07182d;color:white;border:1px solid #244a78;border-radius:12px;padding:12px}
.core{width:135px;height:135px;border-radius:50%;border:3px solid #6d5dfc;display:flex;align-items:center;justify-content:center;margin:20px auto;font-size:24px;font-weight:bold;box-shadow:0 0 24px #00d084}
.box{background:#102a4d;padding:12px;border-radius:12px;margin:8px 0}
.small{color:#9fb3c8}
</style>
</head>
<body>
<div class="wrap">
  <div class="card">
    <h2>KRXA V49 통화형 여행 통역</h2>
    <p class="small">사용자 A ⇄ WebRTC ⇄ 사용자 B / KRXA = 연결 + 통역</p>
    <div class="core" id="core">KRXA</div>
    <input id="room" value="travel-room-1">
    <input id="user" value="">
    <button onclick="startCall()">통화 연결</button>
    <button onclick="recordTranslate()">음성 통역</button>
    <button onclick="sendText()">텍스트 통역</button>
    <p id="status">대기</p>
  </div>

  <div class="card">
    <h3>대화 / 통역</h3>
    <textarea id="text">안녕하세요. 이 근처 지하철역이 어디인가요?</textarea>
    <div id="chat"></div>
    <audio id="remoteAudio" autoplay controls></audio>
    <audio id="ttsAudio" controls></audio>
  </div>

  <div class="card">
    <a style="color:#8ab4ff" href="/admin">ADMIN</a> |
    <a style="color:#8ab4ff" href="/api/state">STATE</a> |
    <a style="color:#8ab4ff" href="/history?room_id=travel-room-1">HISTORY</a>
  </div>
</div>

<script>
let ws, pc, localStream;
let myUser = "user-" + Math.random().toString(16).slice(2,6);
document.getElementById("user").value = myUser;

function room(){ return document.getElementById("room").value; }
function log(t){ document.getElementById("chat").innerHTML += "<div class='box'>"+t+"</div>"; }
function status(t){ document.getElementById("status").innerText=t; }

async function startCall(){
  status("마이크 연결 중...");
  localStream = await navigator.mediaDevices.getUserMedia({audio:true});
  pc = new RTCPeerConnection({iceServers:[{urls:"stun:stun.l.google.com:19302"}]});
  localStream.getTracks().forEach(track=>pc.addTrack(track, localStream));

  pc.ontrack = e => {
    document.getElementById("remoteAudio").srcObject = e.streams[0];
  };

  ws = new WebSocket((location.protocol==="https:"?"wss://":"ws://")+location.host+"/ws/signal?room="+encodeURIComponent(room())+"&user="+encodeURIComponent(myUser));

  ws.onmessage = async (ev)=>{
    const msg = JSON.parse(ev.data);
    if(msg.type==="joined"){
      status("방 입장: "+msg.room+" / "+msg.user);
      log("KRXA 연결됨. 다른 사용자도 같은 room으로 접속하세요.");
    }
    if(msg.type==="offer"){
      await pc.setRemoteDescription(msg.payload);
      const answer = await pc.createAnswer();
      await pc.setLocalDescription(answer);
      ws.send(JSON.stringify({type:"answer",payload:answer}));
    }
    if(msg.type==="answer"){
      await pc.setRemoteDescription(msg.payload);
    }
    if(msg.type==="ice"){
      try{ await pc.addIceCandidate(msg.payload); }catch(e){}
    }
  };

  pc.onicecandidate = e => {
    if(e.candidate && ws && ws.readyState===1){
      ws.send(JSON.stringify({type:"ice",payload:e.candidate}));
    }
  };

  setTimeout(async ()=>{
    const offer = await pc.createOffer();
    await pc.setLocalDescription(offer);
    ws.send(JSON.stringify({type:"offer",payload:offer}));
  }, 1000);
}

async function sendText(){
  const text = document.getElementById("text").value;
  log("<b>입력:</b> "+text);
  const fd = new FormData();
  fd.append("text", text);
  fd.append("room_id", room());
  const r = await fetch("/api/translate", {method:"POST", body:fd});
  const j = await r.json();
  log("<b>KRXA 통역:</b> "+j.translated);
  await playTTS(j.translated);
}

async function playTTS(text){
  const fd = new FormData();
  fd.append("text", text);
  const r = await fetch("/api/tts", {method:"POST", body:fd});
  const blob = await r.blob();
  const url = URL.createObjectURL(blob);
  const a = document.getElementById("ttsAudio");
  a.src = url;
  a.play();
}

async function recordTranslate(){
  const stream = await navigator.mediaDevices.getUserMedia({audio:true});
  const mr = new MediaRecorder(stream);
  let chunks=[];
  mr.ondataavailable=e=>chunks.push(e.data);
  mr.onstop=async()=>{
    const blob = new Blob(chunks,{type:"audio/webm"});
    const fd = new FormData();
    fd.append("file", blob, "voice.webm");

    const sr = await fetch("/api/stt", {method:"POST", body:fd});
    const sj = await sr.json();
    log("<b>음성 입력:</b> "+sj.text);

    const tf = new FormData();
    tf.append("text", sj.text);
    tf.append("room_id", room());
    const tr = await fetch("/api/translate", {method:"POST", body:tf});
    const tj = await tr.json();
    log("<b>KRXA 통역:</b> "+tj.translated);
    await playTTS(tj.translated);
  };
  mr.start();
  status("3초 녹음 중...");
  setTimeout(()=>{mr.stop();status("녹음 완료");},3000);
}
</script>
</body>
</html>
"""


@app.get("/admin", response_class=HTMLResponse)
def admin():
    return f"""
<html><body style="background:#071426;color:white;font-family:Arial;padding:20px">
<h2>KRXA V49 관제</h2>
<p><a style="color:#8ab4ff" href="/user">USER/CALL</a></p>
<h3>Rooms</h3>
<pre>{html.escape(json.dumps(ROOMS, ensure_ascii=False, indent=2, default=str))}</pre>
<h3>Logs</h3>
<pre>{html.escape(json.dumps(LOGS[-50:], ensure_ascii=False, indent=2))}</pre>
</body></html>
"""


@app.get("/verify", response_class=HTMLResponse)
def verify():
    return """
<h2>KRXA V49 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/user">user/call</a></li>
<li><a href="/admin">admin</a></li>
<li><a href="/api/state">api/state</a></li>
</ul>
"""
