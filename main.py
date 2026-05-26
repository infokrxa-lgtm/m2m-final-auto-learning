from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from krxa_engine import process
from krxa_travel import get_cards

app = FastAPI()

@app.post("/chat")
def chat(text: str = Form(...), service: str = Form("free")):
    result = process(text)
    cards = get_cards(text, service)
    return {"result": result, "cards": cards}

@app.get("/")
def root():
    return {"ok": True, "version": "V60-STABLE"}

@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<html><body>
<h1>KRXA 여행 도우미</h1>
<p><a href="/app?service=food" target="_blank">🍴 맛집 찾기</a></p>
<p><a href="/app?service=map" target="_blank">📍 길찾기</a></p>
<p><a href="/app?service=hotel" target="_blank">🏨 숙소</a></p>
</body></html>
"""

@app.get("/app", response_class=HTMLResponse)
def app_ui(service: str = "free"):
    page = """
<html>
<body>
<h1>__SERVICE__ 서비스</h1>

<textarea id="t" style="width:300px;height:80px;" placeholder="사용자 입력 언어로 입력하세요"></textarea><br>
<button onclick="send()">전송</button>

<div id="chat"></div>
<div id="cards"></div>

<script>
async function send(){
    let input = document.getElementById("t");
    let text = input.value.trim();
    if(!text){ return; }
    input.value = "";

    let fd = new FormData();
    fd.append("text", text);
    fd.append("service", "__SERVICE__");

    let r = await fetch("/chat", {
        method: "POST",
        body: fd
    });
    let j = await r.json();

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
</script>

<br><a href="/user">← 사용자 화면으로 돌아가기</a>
</body>
</html>
"""
    return page.replace("__SERVICE__", service)

@app.get("/control", response_class=HTMLResponse)
def control():
    return """
<html><body>
<h1>KRXA CONTROL</h1>
<p>관제 화면</p>
</body></html>
"""

@app.get("/dev", response_class=HTMLResponse)
def dev():
    return """
<html><body>
<h1>KRXA DEV</h1>
<p>개발자 화면</p>
</body></html>
"""
