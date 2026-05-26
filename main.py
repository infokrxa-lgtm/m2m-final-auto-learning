import os, json, html, uuid, time
from pathlib import Path
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="KRXA V40")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA = Path("storage")
DATA.mkdir(exist_ok=True)

SESSIONS = {}
ROOMS = {}
WAITING = []

# --------------------------
# STATE
# --------------------------
def create_session():
    sid = "user-" + uuid.uuid4().hex[:8]
    SESSIONS[sid] = {
        "state": "INIT",
        "room": None,
        "last": time.time()
    }
    return sid

def join_queue(sid):
    if sid not in WAITING:
        WAITING.append(sid)
        SESSIONS[sid]["state"] = "QUEUE"

    if len(WAITING) >= 2:
        a = WAITING.pop(0)
        b = WAITING.pop(0)

        rid = "room-" + uuid.uuid4().hex[:6]
        ROOMS[rid] = {
            "users": [a, b],
            "messages": []
        }

        SESSIONS[a]["room"] = rid
        SESSIONS[b]["room"] = rid
        SESSIONS[a]["state"] = "CONNECTED"
        SESSIONS[b]["state"] = "CONNECTED"

# --------------------------
# API
# --------------------------
class Msg(BaseModel):
    session_id: str
    text: str

@app.get("/api/join")
def api_join():
    sid = create_session()
    join_queue(sid)
    return {"session_id": sid}

@app.get("/api/state")
def api_state(session_id: str):
    return SESSIONS.get(session_id, {})

@app.post("/api/send")
def api_send(m: Msg):
    sid = m.session_id
    rid = SESSIONS.get(sid, {}).get("room")

    if not rid:
        return {"error": "no room"}

    users = ROOMS[rid]["users"]
    target = users[0] if users[1] == sid else users[1]

    # GPT 번역
    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role":"user","content":m.text}]
    )
    translated = r.choices[0].message.content

    msg = {
        "from": sid,
        "to": target,
        "text": m.text,
        "translated": translated,
        "time": time.time()
    }

    ROOMS[rid]["messages"].append(msg)

    return {"ok": True}

@app.get("/api/poll")
def api_poll(session_id: str):
    rid = SESSIONS.get(session_id, {}).get("room")
    if not rid:
        return {"messages":[]}

    msgs = [m for m in ROOMS[rid]["messages"] if m["to"] == session_id]
    return {"messages": msgs}

# --------------------------
# USER UI
# --------------------------
@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<h2>KRXA V40 USER</h2>
<button onclick="join()">입장</button>
<p id="status"></p>
<div id="chat"></div>
<input id="msg"><button onclick="send()">전송</button>

<script>
let sid=null

async function join(){
  let r=await fetch('/api/join')
  let j=await r.json()
  sid=j.session_id
  document.getElementById('status').innerText="세션:"+sid
  setInterval(poll,1000)
}

async function send(){
  let t=document.getElementById('msg').value
  await fetch('/api/send',{
    method:'POST',
    headers:{'Content-Type':'application/json'},
    body:JSON.stringify({session_id:sid,text:t})
  })
}

async function poll(){
  let r=await fetch('/api/poll?session_id='+sid)
  let j=await r.json()
  let div=document.getElementById('chat')
  j.messages.forEach(m=>{
    div.innerHTML += "<p><b>상대:</b>"+m.translated+"</p>"
  })
}
</script>
"""

# --------------------------
# ADMIN
# --------------------------
@app.get("/admin", response_class=HTMLResponse)
def admin():
    return f"""
<h2>ADMIN</h2>
<pre>{json.dumps(SESSIONS, indent=2)}</pre>
<pre>{json.dumps(ROOMS, indent=2)}</pre>
"""

# --------------------------
# DEV FILE
# --------------------------
@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = Path(".") if not path else Path(path)
    if root.is_file():
        content = html.escape(root.read_text())
        return f"""
<form method="post" action="/dev/save">
<input name="path" value="{path}">
<textarea name="content" style="width:100%;height:80vh;">{content}</textarea>
<button>save</button>
</form>
"""
    items = ""
    for p in root.iterdir():
        items += f"<li><a href='/dev?path={p}'>{p}</a></li>"
    return f"<ul>{items}</ul>"

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    Path(path).write_text(content)
    return RedirectResponse("/dev")
