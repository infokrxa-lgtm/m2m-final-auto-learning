import os, json, uuid, time
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from openai import OpenAI

app = FastAPI(title="KRXA V41 REALTIME")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------
# MEMORY
# ------------------------
SESSIONS = {}
ROOMS = {}

# ------------------------
# SESSION / ROOM
# ------------------------
def create_session():
    sid = "user-" + uuid.uuid4().hex[:6]
    SESSIONS[sid] = {
        "room": None,
        "ws": None
    }
    return sid

WAITING = []

def match_user(sid):
    WAITING.append(sid)

    if len(WAITING) >= 2:
        a = WAITING.pop(0)
        b = WAITING.pop(0)

        rid = "room-" + uuid.uuid4().hex[:6]
        ROOMS[rid] = [a, b]

        SESSIONS[a]["room"] = rid
        SESSIONS[b]["room"] = rid

        return rid
    return None

# ------------------------
# ROOT
# ------------------------
@app.get("/")
def root():
    return {"ok": True, "version": "V41"}

# ------------------------
# USER UI
# ------------------------
@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<h2>KRXA V41 REALTIME</h2>
<button onclick="connect()">연결 시작</button>
<p id="status"></p>

<div id="chat"></div>

<input id="msg">
<button onclick="send()">전송</button>

<script>
let ws;
let sid=null;

function log(t){
  document.getElementById("chat").innerHTML += "<p>"+t+"</p>";
}

function connect(){
  ws = new WebSocket("wss://" + location.host + "/ws");

  ws.onmessage = (e)=>{
    let d = JSON.parse(e.data);

    if(d.type==="init"){
      sid=d.sid;
      document.getElementById("status").innerText="세션:"+sid;
    }

    if(d.type==="match"){
      log("상대 연결됨");
    }

    if(d.type==="msg"){
      log("<b>상대:</b> "+d.text);
    }
  };
}

function send(){
  let t=document.getElementById("msg").value;
  log("<b>나:</b> "+t);
  ws.send(JSON.stringify({text:t}));
}
</script>
"""

# ------------------------
# WEBSOCKET
# ------------------------
@app.websocket("/ws")
async def websocket(ws: WebSocket):
    await ws.accept()

    sid = create_session()
    SESSIONS[sid]["ws"] = ws

    await ws.send_json({"type":"init","sid":sid})

    rid = match_user(sid)

    if rid:
        for u in ROOMS[rid]:
            other_ws = SESSIONS[u]["ws"]
            await other_ws.send_json({"type":"match"})

    try:
        while True:
            data = await ws.receive_json()
            text = data.get("text","")

            rid = SESSIONS[sid]["room"]
            if not rid:
                continue

            users = ROOMS[rid]
            target = users[0] if users[1]==sid else users[1]

            # GPT 번역
            r = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role":"user","content":text}]
            )
            translated = r.choices[0].message.content

            target_ws = SESSIONS[target]["ws"]

            await target_ws.send_json({
                "type":"msg",
                "text": translated
            })

    except WebSocketDisconnect:
        pass
