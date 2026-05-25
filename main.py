import os, json, html, uuid
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="KRXA V38 FINAL")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

ROOT = Path(".").resolve()
DATA = Path("storage")
DATA.mkdir(exist_ok=True)

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

PROMPT = """
KRXA V38 FINAL
- ChatGPT first call.
- "첨부파일" = context trigger.
- "여기서부터 통역시작하자" = interpretation mode ON.
- Maintain natural conversation flow.
- Auto-detect 13 languages.
- Keep session memory.
- KRXA is router; ChatGPT is brain.
"""

class ChatReq(BaseModel):
    text: str
    session_id: str = "default"

def clean_sid(s):
    return "".join(c for c in s if c.isalnum() or c in "-_")[:80] or "default"

def hfile(sid):
    return DATA / f"history_{clean_sid(sid)}.json"

def load_history(sid="default"):
    f = hfile(sid)
    if not f.exists():
        return []
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except Exception:
        return []

def save_history(user, assistant, sid="default"):
    h = load_history(sid)
    h.append({"user": user, "assistant": assistant})
    hfile(sid).write_text(json.dumps(h[-80:], ensure_ascii=False, indent=2), encoding="utf-8")

def messages(text, sid="default"):
    m = [{"role": "system", "content": PROMPT}]
    for x in load_history(sid)[-10:]:
        m.append({"role": "user", "content": x.get("user","")})
        m.append({"role": "assistant", "content": x.get("assistant","")})
    m.append({"role": "user", "content": text})
    return m

def safe_path(p):
    t = (ROOT / p).resolve()
    if not str(t).startswith(str(ROOT)):
        raise ValueError("invalid path")
    return t

@app.get("/")
def home():
    return {"ok": True, "version": "V38-FINAL", "routes": ["/user","/dev","/admin","/verify"]}

@app.get("/health")
def health():
    return {"ok": True, "version": "V38-FINAL"}

@app.get("/api/state")
def api_state():
    return {
        "ok": True,
        "version": "V38-FINAL",
        "session_state": "ALIVE_HOME",
        "queue_state": "READY",
        "presence_state": "ONLINE",
        "reconnect_state": "STABLE",
        "recovery_state": "NORMAL",
        "voice_ai_ready": True
    }

@app.post("/api/chat")
@app.post("/chat")
def chat(req: ChatReq):
    r = client.chat.completions.create(model=TEXT_MODEL, messages=messages(req.text, req.session_id))
    ans = r.choices[0].message.content or ""
    save_history(req.text, ans, req.session_id)
    return {"ok": True, "session_id": req.session_id, "response": ans}

@app.post("/api/tts")
@app.post("/tts")
def tts(req: ChatReq):
    audio = client.audio.speech.create(model=TTS_MODEL, voice="coral", input=req.text)
    return Response(content=audio.read(), media_type="audio/mpeg")

@app.post("/api/voice")
@app.post("/voice")
async def voice(file: UploadFile = File(...), session_id: str = Form("default")):
    suffix = Path(file.filename or "voice.webm").suffix or ".webm"
    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    try:
        with open(tmp_path, "rb") as f:
            tr = client.audio.transcriptions.create(model=STT_MODEL, file=f)
        text = tr.text
        r = client.chat.completions.create(model=TEXT_MODEL, messages=messages(text, session_id))
        ans = r.choices[0].message.content or ""
        save_history(text, ans, session_id)
        return {"ok": True, "session_id": session_id, "text": text, "response": ans}
    finally:
        try: os.remove(tmp_path)
        except Exception: pass

@app.get("/history")
def history(session_id: str = "default"):
    return {"ok": True, "session_id": session_id, "history": load_history(session_id)}

@app.get("/user", response_class=HTMLResponse)
@app.get("/ui", response_class=HTMLResponse)
def user_ui():
    return """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;max-width:900px;margin:24px auto;padding:12px}
textarea{width:100%;height:90px;font-size:16px}
button{padding:12px 16px;margin:5px;font-size:16px}
.box{border:1px solid #ddd;padding:12px;margin-top:12px;white-space:pre-wrap}
</style></head><body>
<h2>KRXA V38 말대말 사용자 UI</h2>
<p><a href="/dev">DEV</a> | <a href="/admin">ADMIN</a> | <a href="/verify">VERIFY</a></p>
<p>Session: <span id="sid"></span></p>
<textarea id="text">여기서부터 통역시작하자. hello</textarea><br>
<button onclick="send()">텍스트 전송</button>
<button onclick="rec()">3초 녹음</button>
<button onclick="hist()">히스토리</button>
<div class="box"><b>User/STT</b><div id="user"></div></div>
<div class="box"><b>ChatGPT</b><div id="out"></div></div>
<audio id="audio" controls></audio>
<script>
let sid=localStorage.getItem("krxa_sid")||("user-"+Math.random().toString(16).slice(2));
localStorage.setItem("krxa_sid",sid); document.getElementById("sid").innerText=sid;
async function speak(t){if(!t)return;let r=await fetch('/api/tts',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,session_id:sid})});let b=await r.blob();let u=URL.createObjectURL(b);let a=document.getElementById('audio');a.src=u;a.play();}
async function send(){let t=document.getElementById('text').value;document.getElementById('user').innerText=t;let r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:t,session_id:sid})});let j=await r.json();document.getElementById('out').innerText=j.response||JSON.stringify(j);await speak(j.response);}
async function rec(){let s=await navigator.mediaDevices.getUserMedia({audio:true});let mr=new MediaRecorder(s);let chunks=[];mr.ondataavailable=e=>chunks.push(e.data);mr.onstop=async()=>{let blob=new Blob(chunks,{type:'audio/webm'});let form=new FormData();form.append('file',blob,'voice.webm');form.append('session_id',sid);let r=await fetch('/api/voice',{method:'POST',body:form});let j=await r.json();document.getElementById('user').innerText=j.text||'';document.getElementById('out').innerText=j.response||JSON.stringify(j);await speak(j.response);};mr.start();setTimeout(()=>mr.stop(),3000);}
async function hist(){let r=await fetch('/history?session_id='+encodeURIComponent(sid));let j=await r.json();document.getElementById('out').innerText=JSON.stringify(j.history,null,2);}
</script></body></html>
"""

@app.get("/admin", response_class=HTMLResponse)
def admin():
    return """
<html><body><h2>KRXA V38 관제 UI</h2>
<p><a href="/user">USER</a> | <a href="/dev">DEV</a> | <a href="/verify">VERIFY</a></p>
<pre id="state">loading...</pre>
<script>
async function load(){let r=await fetch('/api/state');let j=await r.json();document.getElementById('state').innerText=JSON.stringify(j,null,2);}
load(); setInterval(load,5000);
</script></body></html>
"""

@app.get("/verify", response_class=HTMLResponse)
def verify():
    return """
<html><body><h2>KRXA V38 VERIFY</h2>
<ul>
<li><a href="/health">health</a></li>
<li><a href="/api/state">api/state</a></li>
<li><a href="/user">user</a></li>
<li><a href="/dev">dev</a></li>
<li><a href="/admin">admin</a></li>
</ul></body></html>
"""

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)
    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        name = html.escape(path)
        return (
            "<html><body><h2>KRXA DEV EDIT</h2>"
            f"<p>{name}</p><form method='post' action='/dev/save'>"
            f"<input type='hidden' name='path' value='{name}'>"
            f"<textarea name='content' style='width:100%;height:70vh;'>{content}</textarea>"
            "<br><button type='submit'>SAVE</button></form>"
            "<p><a href='/dev'>FILE LIST</a> | <a href='/user'>USER</a></p></body></html>"
        )
    items=[]
    for item in sorted(root.iterdir()):
        rel=str(item.relative_to(ROOT)); label=html.escape(rel)
        icon="[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")
    return "<html><body><h2>KRXA DEV FILES</h2><p><a href='/user'>USER</a> | <a href='/admin'>ADMIN</a></p><ul>"+ "".join(items) +"</ul></body></html>"

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    safe_path(path).write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)
