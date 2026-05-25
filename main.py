import os, json
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, Response, HTMLResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="KRXA V35 UI VOICE AI")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path("storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

INVITE_PROMPT = """
[KRXA V35.0]

Rules:
- KRXA always calls ChatGPT first.
- "여기서부터 통역시작하자" means interpretation mode ON.
- Detect language automatically.
- Support 13 languages: ko,en,ja,zh,es,fr,de,vi,th,id,ar,ru,pt.
- Keep answers clear and natural.
- Use history memory.
"""

class ChatRequest(BaseModel):
    text: str

def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(user_text, assistant_text):
    history = load_history()
    history.append({"user": user_text, "assistant": assistant_text})
    HISTORY_FILE.write_text(
        json.dumps(history[-50:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

def build_messages(user_text):
    messages = [{"role": "system", "content": INVITE_PROMPT}]
    for item in load_history()[-10:]:
        messages.append({"role": "user", "content": item.get("user", "")})
        messages.append({"role": "assistant", "content": item.get("assistant", "")})
    messages.append({"role": "user", "content": user_text})
    return messages

@app.get("/")
def home():
    return {"service": "KRXA V35 UI VOICE AI", "ok": True}

@app.get("/health")
def health():
    return {"ok": True, "version": "V35.0-UI-VOICE-AI"}

@app.get("/chat-test")
def chat_test(q: str = "여기서부터 통역시작하자. hello"):
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=build_messages(q),
    )
    answer = response.choices[0].message.content or ""
    save_history(q, answer)
    return {"ok": True, "input": q, "response": answer}

@app.post("/chat")
def chat(req: ChatRequest):
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=build_messages(req.text),
    )
    answer = response.choices[0].message.content or ""
    save_history(req.text, answer)
    return {"ok": True, "input": req.text, "response": answer}

@app.post("/tts")
def tts(req: ChatRequest):
    audio = client.audio.speech.create(
        model=TTS_MODEL,
        voice="coral",
        input=req.text,
    )
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=audio_file,
            )

        user_text = transcript.text

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=build_messages(user_text),
        )
        answer = response.choices[0].message.content or ""
        save_history(user_text, answer)

        return {"ok": True, "text": user_text, "response": answer}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@app.get("/history")
def history():
    return {"ok": True, "history": load_history()}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<!doctype html>
<html>
<head>
<meta charset="utf-8"/>
<title>KRXA V35 Voice UI</title>
<style>
body { font-family: Arial; max-width: 760px; margin: 40px auto; }
button { padding: 12px 18px; margin: 6px; font-size: 16px; }
textarea { width: 100%; height: 90px; }
.box { border: 1px solid #ddd; padding: 14px; margin-top: 12px; white-space: pre-wrap; }
</style>
</head>
<body>
<h2>KRXA V35 Voice AI</h2>

<textarea id="text">여기서부터 통역시작하자. hello</textarea><br/>
<button onclick="sendText()">텍스트 전송</button>
<button id="recBtn" onclick="toggleRec()">🎙 녹음 시작</button>
<button onclick="loadHistory()">히스토리</button>

<div class="box"><b>STT/User:</b><div id="user"></div></div>
<div class="box"><b>ChatGPT:</b><div id="answer"></div></div>
<audio id="audio" controls></audio>

<script>
let mediaRecorder;
let chunks = [];
let recording = false;

async function sendText() {
  const text = document.getElementById("text").value;
  document.getElementById("user").innerText = text;

  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text})
  });
  const data = await res.json();
  document.getElementById("answer").innerText = data.response || JSON.stringify(data);
  await playTTS(data.response || "");
}

async function toggleRec() {
  if (!recording) {
    const stream = await navigator.mediaDevices.getUserMedia({audio: true});
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = uploadVoice;
    mediaRecorder.start();
    recording = true;
    document.getElementById("recBtn").innerText = "⏹ 녹음 종료";
  } else {
    mediaRecorder.stop();
    recording = false;
    document.getElementById("recBtn").innerText = "🎙 녹음 시작";
  }
}

async function uploadVoice() {
  const blob = new Blob(chunks, {type: "audio/webm"});
  const form = new FormData();
  form.append("file", blob, "voice.webm");

  const res = await fetch("/voice", {method: "POST", body: form});
  const data = await res.json();

  document.getElementById("user").innerText = data.text || "";
  document.getElementById("answer").innerText = data.response || JSON.stringify(data);

  await playTTS(data.response || "");
}

async function playTTS(text) {
  if (!text) return;
  const res = await fetch("/tts", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({text})
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = document.getElementById("audio");
  audio.src = url;
  audio.play();
}
from fastapi import Form
from fastapi.responses import RedirectResponse
import html

SAFE_ROOT = Path(".").resolve()

def safe_path(p: str):
    target = (SAFE_ROOT / p).resolve()
    if not str(target).startswith(str(SAFE_ROOT)):
        raise ValueError("Invalid path")
    return target

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)

    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        safe_name = html.escape(path)
        return f"""<!doctype html>
<html><body>
<h2>KRXA DEV EDIT</h2>
<p>{safe_name}</p>
<form method="post" action="/dev/save">
<input type="hidden" name="path" value="{safe_name}">
<textarea name="content" style="width:100%;height:70vh;">{content}</textarea>
<br><button type="submit">저장</button>
</form>
<p><a href="/dev">파일 목록</a></p>
</body></html>"""

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(SAFE_ROOT))
        icon = "📁" if item.is_dir() else "📄"
        items.append(f'<li><a href="/dev?path={html.escape(rel)}">{icon} {html.escape(rel)}</a></li>')

    return f"""<!doctype html>
<html><body>
<h2>KRXA DEV FILES</h2>
<p><a href="/ui">🎙 Voice AI UI</a></p>
<ul>{''.join(items)}</ul>
</body></html>"""

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    target = safe_path(path)
    target.write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)
