import os, json, html
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="KRXA V36 FULL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SAFE_ROOT = Path(".").resolve()
DATA_DIR = Path("storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

PROMPT = """
KRXA V36:
- ChatGPT first call.
- "여기서부터 통역시작하자" = interpretation mode ON.
- Auto-detect language.
- Support 13 languages.
- Keep memory loop.
- Answer naturally and briefly.
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

def save_history(user, assistant):
    h = load_history()
    h.append({"user": user, "assistant": assistant})
    HISTORY_FILE.write_text(json.dumps(h[-50:], ensure_ascii=False, indent=2), encoding="utf-8")

def messages(text):
    m = [{"role": "system", "content": PROMPT}]
    for item in load_history()[-10:]:
        m.append({"role": "user", "content": item.get("user", "")})
        m.append({"role": "assistant", "content": item.get("assistant", "")})
    m.append({"role": "user", "content": text})
    return m

def safe_path(p: str):
    target = (SAFE_ROOT / p).resolve()
    if not str(target).startswith(str(SAFE_ROOT)):
        raise ValueError("Invalid path")
    return target

@app.get("/")
def home():
    return {"ok": True, "service": "KRXA V36 FULL"}

@app.get("/health")
def health():
    return {"ok": True, "version": "V36-FULL"}

@app.post("/chat")
def chat(req: ChatRequest):
    r = client.chat.completions.create(model=TEXT_MODEL, messages=messages(req.text))
    ans = r.choices[0].message.content or ""
    save_history(req.text, ans)
    return {"ok": True, "input": req.text, "response": ans}

@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    suffix = Path(file.filename or "voice.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            tr = client.audio.transcriptions.create(model=STT_MODEL, file=f)
        text = tr.text
        r = client.chat.completions.create(model=TEXT_MODEL, messages=messages(text))
        ans = r.choices[0].message.content or ""
        save_history(text, ans)
        return {"ok": True, "text": text, "response": ans}
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass

@app.post("/tts")
def tts(req: ChatRequest):
    audio = client.audio.speech.create(model=TTS_MODEL, voice="coral", input=req.text)
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.get("/history")
def history():
    return {"ok": True, "history": load_history()}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
<html><body style="font-family:Arial;max-width:760px;margin:40px auto;">
<h2>KRXA V36 Voice AI</h2>
<p><a href="/dev">DEV FILES</a></p>
<textarea id="text" style="width:100%;height:90px;">여기서부터 통역시작하자. hello</textarea><br><br>
<button onclick="send()">텍스트 전송</button>
<button onclick="rec()">3초 녹음</button>
<button onclick="hist()">히스토리</button>
<div style="border:1px solid #ddd;padding:12px;margin-top:12px;"><b>User/STT</b><pre id="user"></pre></div>
<div style="border:1px solid #ddd;padding:12px;margin-top:12px;"><b>ChatGPT</b><pre id="out"></pre></div>
<audio id="audio" controls></audio>
<script>
async function speak(t){
  if(!t) return;
  let r = await fetch('/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
  let b = await r.blob();
  let u = URL.createObjectURL(b);
  let a = document.getElementById('audio');
  a.src = u;
  a.play();
}
async function send(){
  let t=document.getElementById('text').value;
  document.getElementById('user').innerText=t;
  let r=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t})});
  let j=await r.json();
  document.getElementById('out').innerText=j.response || JSON.stringify(j);
  await speak(j.response);
}
async function rec(){
  let s=await navigator.mediaDevices.getUserMedia({audio:true});
  let mr=new MediaRecorder(s);
  let chunks=[];
  mr.ondataavailable=e=>chunks.push(e.data);
  mr.onstop=async()=>{
    let blob=new Blob(chunks,{type:'audio/webm'});
    let form=new FormData();
    form.append('file',blob,'voice.webm');
    let r=await fetch('/voice',{method:'POST',body:form});
    let j=await r.json();
    document.getElementById('user').innerText=j.text || '';
    document.getElementById('out').innerText=j.response || JSON.stringify(j);
    await speak(j.response);
  };
  mr.start();
  setTimeout(()=>mr.stop(),3000);
}
async function hist(){
  let r=await fetch('/history');
  let j=await r.json();
  document.getElementById('out').innerText=JSON.stringify(j.history,null,2);
}
</script>
</body></html>
"""

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)
    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        safe_name = html.escape(path)
        return (
            "<html><body><h2>KRXA DEV EDIT</h2>"
            f"<p>{safe_name}</p>"
            "<form method='post' action='/dev/save'>"
            f"<input type='hidden' name='path' value='{safe_name}'>"
            f"<textarea name='content' style='width:100%;height:70vh;'>{content}</textarea>"
            "<br><button type='submit'>SAVE</button></form>"
            "<p><a href='/dev'>FILE LIST</a></p></body></html>"
        )

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(SAFE_ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")
    return (
        "<html><body><h2>KRXA DEV FILES</h2>"
        "<p><a href='/ui'>Voice AI UI</a></p>"
        f"<ul>{''.join(items)}</ul></body></html>"
    )

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    target = safe_path(path)
    target.write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)
