from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import html

app = FastAPI(title="KRXA SAFE DEV UI")

SAFE_ROOT = Path(".").resolve()

def safe_path(p: str):
    target = (SAFE_ROOT / p).resolve()
    if not str(target).startswith(str(SAFE_ROOT)):
        raise ValueError("Invalid path")
    return target

@app.get("/")
def home():
    return {"service": "KRXA SAFE DEV UI", "ok": True}

@app.get("/health")
def health():
    return {"ok": True, "version": "SAFE-DEV-RESET"}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return "<h2>KRXA Voice AI UI</h2><p>Reset OK</p><p><a href='/dev'>DEV FILES</a></p>"

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)

    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        safe_name = html.escape(path)
        return (
            "<html><body>"
            "<h2>KRXA DEV EDIT</h2>"
            f"<p>{safe_name}</p>"
            "<form method='post' action='/dev/save'>"
            f"<input type='hidden' name='path' value='{safe_name}'>"
            f"<textarea name='content' style='width:100%;height:70vh;'>{content}</textarea>"
            "<br><button type='submit'>SAVE</button>"
            "</form>"
            "<p><a href='/dev'>FILE LIST</a></p>"
            "</body></html>"
        )

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(SAFE_ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")

    return (
        "<html><body>"
        "<h2>KRXA DEV FILES</h2>"
        "<p><a href='/ui'>Voice AI UI</a></p>"
        f"<ul>{''.join(items)}</ul>"
        "</body></html>"
    )

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    target = safe_path(path)
    target.write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)

from fastapi import UploadFile, File
from fastapi.responses import HTMLResponse
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return """
    <h2>KRXA Voice AI</h2>
    <textarea id="text" style="width:100%;height:80px;">여기서부터 통역시작하자. hello</textarea><br/>
    <button onclick="send()">전송</button>
    <button onclick="rec()">🎤 녹음</button>
    <div id="out"></div>
    <audio id="audio" controls></audio>

    <script>
    async function send(){
        let t = document.getElementById("text").value;
        let r = await fetch("/chat",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:t})});
        let j = await r.json();
        document.getElementById("out").innerText = j.response;

        let tts = await fetch("/tts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:j.response})});
        let blob = await tts.blob();
        let url = URL.createObjectURL(blob);
        document.getElementById("audio").src = url;
    }

    let recStream, mediaRecorder, chunks=[];
    async function rec(){
        recStream = await navigator.mediaDevices.getUserMedia({audio:true});
        mediaRecorder = new MediaRecorder(recStream);
        chunks=[];
        mediaRecorder.ondataavailable=e=>chunks.push(e.data);
        mediaRecorder.onstop=upload;
        mediaRecorder.start();
        setTimeout(()=>mediaRecorder.stop(),3000);
    }

    async function upload(){
        let blob=new Blob(chunks,{type:"audio/webm"});
        let form=new FormData();
        form.append("file",blob,"voice.webm");
        let r=await fetch("/voice",{method:"POST",body:form});
        let j=await r.json();
        document.getElementById("out").innerText=j.response;

        let tts = await fetch("/tts",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({text:j.response})});
        let blob2 = await tts.blob();
        let url = URL.createObjectURL(blob2);
        document.getElementById("audio").src = url;
    }
    </script>
    """
