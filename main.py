from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from krxa_engine import process
from krxa_travel import get_cards
from krxa_store import (
    new_id,
    load_history,
    save_turn,
    clear_history,
    load_logs
)

app = FastAPI()


@app.post("/chat")
def chat(
    text: str = Form(...),
    service: str = Form("free"),
    session_id: str = Form("")
):
    if not session_id:
        session_id = new_id("session")

    history = load_history(session_id, limit=12)
    result = process(text, history=history, service=service)
    cards = get_cards(text, service)

    save_turn(
        session_id=session_id,
        user_text=text,
        krxa_text=result,
        service=service,
        cards=cards
    )

    return {
        "result": result,
        "cards": cards,
        "session_id": session_id
    }


@app.post("/history/clear")
def history_clear(session_id: str = Form(...)):
    clear_history(session_id)
    return {"ok": True, "session_id": session_id}


@app.get("/history")
def history(session_id: str):
    return {
        "ok": True,
        "session_id": session_id,
        "history": load_history(session_id, limit=100)
    }


@app.get("/api/state")
def state():
    return {
        "ok": True,
        "version": "V61-MEMORY",
        "logs": load_logs(80)
    }


@app.get("/")
def root():
    return {"ok": True, "version": "V61-MEMORY"}


@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:Arial;background:#eef2f7;margin:0}
.wrap{max-width:480px;margin:auto;padding:24px}
.card{background:white;padding:20px;margin:14px 0;border-radius:18px;box-shadow:0 6px 18px rgba(0,0,0,.08);cursor:pointer}
h1{text-align:center}
</style>
</head>
<body>
<div class="wrap">
<h1>KRXA 여행 도우미</h1>

<div class="card" onclick="openService('food')">🍴 맛집 찾기</div>
<div class="card" onclick="openService('map')">📍 길찾기</div>
<div class="card" onclick="openService('hotel')">🏨 숙소</div>

</div>

<script>
function openService(service){
    window.open("/app?service=" + service, "_blank");
}
</script>
</body>
</html>
"""


@app.get("/app", response_class=HTMLResponse)
def app_ui(service: str = "free"):
    page = """
<html>
<body>
<h1>__SERVICE__ 서비스</h1>

<textarea id="t" style="width:300px;height:80px;" placeholder="사용자 입력 언어로 입력하세요"></textarea><br>
<button onclick="send()">전송</button>
<button onclick="clearMemory()">기억 초기화</button>

<div id="chat"></div>
<div id="cards"></div>

<script>
let sessionId = localStorage.getItem("krxa_session_id");
if(!sessionId){
    sessionId = "session-" + Math.random().toString(16).slice(2,10);
    localStorage.setItem("krxa_session_id", sessionId);
}

async function send(){
    let input = document.getElementById("t");
    let text = input.value.trim();
    if(!text){ return; }
    input.value = "";

    let fd = new FormData();
    fd.append("text", text);
    fd.append("service", "__SERVICE__");
    fd.append("session_id", sessionId);

    let r = await fetch("/chat", {
        method: "POST",
        body: fd
    });
    let j = await r.json();

    if(j.session_id){
        sessionId = j.session_id;
        localStorage.setItem("krxa_session_id", sessionId);
    }

    let chat = document.getElementById("chat");
    chat.innerHTML += "<div class='msg'><b>나:</b> " + text + "</div>";
    chat.innerHTML += "<div class='msg'><b>KRXA:</b> " + j.result + "</div>";

    let html = "";
    if(j.cards && j.cards.length > 0){
        j.cards.forEach(function(c){
            if(c.url){
                html += "<div class='card'><a href='" + c.url + "' target='_blank'>" + c.label + "</a></div>";
            } else if(c.text){
                html += "<div class='card'><b>" + c.label + "</b><br>" + c.text + "</div>";
            }
        });
    }
    document.getElementById("cards").innerHTML = html;

    let msgs = chat.querySelectorAll(".msg");
    if(msgs.length > 8){
        msgs[0].remove();
        msgs[1].remove();
    }
}

async function clearMemory(){
    let fd = new FormData();
    fd.append("session_id", sessionId);

    await fetch("/history/clear", {
        method: "POST",
        body: fd
    });

    document.getElementById("chat").innerHTML = "";
    document.getElementById("cards").innerHTML = "";
    alert("KRXA 기억을 초기화했습니다.");
}
</script>

<br><a href="/user">← 사용자 화면으로 돌아가기</a>
<br><a id="historyLink" href="#" onclick="this.href='/history?session_id='+sessionId" target="_blank">기억 보기</a>
</body>
</html>
"""
    return page.replace("__SERVICE__", service)


@app.get("/control", response_class=HTMLResponse)
def control():
    logs = load_logs(80)
    return f"""
<html>
<body>
<h1>KRXA CONTROL</h1>
<p>관제 화면</p>
<pre>{logs}</pre>
</body>
</html>
"""


@app.get("/dev", response_class=HTMLResponse)
def dev():
    return """
<html>
<body>
<h1>KRXA DEV</h1>
<p>개발자 화면</p>
<ul>
<li>main.py</li>
<li>krxa_engine.py</li>
<li>krxa_travel.py</li>
<li>krxa_store.py</li>
</ul>
</body>
</html>
"""
