from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi import Form
from krxa_engine import process
from krxa_travel import get_cards


app = FastAPI()
@app.post("/chat")
def chat(text: str = Form(...)):
    result = process(text)
    cards = get_cards(text)
    return {
        "result": result,
        "cards": cards
    }
@app.get("/")
def root():
    return {"ok": True, "version": "V60"}

# ---------------- USER ----------------
@app.get("/user", response_class=HTMLResponse)
def user():
    return """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#f5f7fb}
.wrap{max-width:480px;margin:auto;padding:20px}
.title{font-size:26px;font-weight:bold}
.card{background:white;padding:20px;margin-top:15px;border-radius:16px;box-shadow:0 4px 12px rgba(0,0,0,0.08);cursor:pointer}
.card:hover{transform:scale(1.02)}
.icon{font-size:24px}
</style>
</head>

<body>
<div class="wrap">

<div class="title">KRXA 여행 도우미</div>

<div class="card" onclick="go('food')">
<div class="icon">🍴</div>
맛집 찾기
</div>

<div class="card" onclick="go('map')">
<div class="icon">📍</div>
길찾기
</div>

<div class="card" onclick="go('hotel')">
<div class="icon">🏨</div>
숙소
</div>

</div>

<script>
function go(s){
 location.href="/app?service="+s;
}
</script>

</body>
</html>
"""

# ---------------- APP ----------------
@app.get("/app", response_class=HTMLResponse)
def app_ui(service: str = "free"):
    return f"""
<html>
<body>
<h1>{service} 서비스</h1>

<textarea id="t" style="width:300px;height:80px;"></textarea><br>
<button onclick="send()">전송</button>

<div id="chat"></div>
<div id="cards"></div>

<script>
async function send(){{
    let text = document.getElementById("t").value;
    let fd = new FormData();
    fd.append("text", text);

    let r = await fetch("/chat", {{
        method: "POST",
        body: fd
    }});
    let j = await r.json();

    document.getElementById("chat").innerHTML += "<p><b>나:</b> " + text + "</p>";
    document.getElementById("chat").innerHTML += "<p><b>KRXA:</b> " + j.result + "</p>";

    let html = "";
    if(j.cards){{
        j.cards.forEach(function(c){{
            if(c.url){{
                html += "<p><a href='" + c.url + "' target='_blank'>" + c.label + "</a></p>";
            }} else {{
                html += "<p>" + c.text + "</p>";
            }}
        }});
    }}
    document.getElementById("cards").innerHTML = html;
}}
</script>

<br><a href="/user">← 돌아가기</a>
</body>
</html>
"""
# ---------------- CONTROL ----------------
@app.get("/control", response_class=HTMLResponse)
def control():
    return """
    <h1>KRXA CONTROL</h1>
    <p>관제 화면</p>
    <ul>
      <li>세션 상태</li>
      <li>로그</li>
      <li>서비스 상태</li>
    </ul>
    """

# ---------------- DEV ----------------
@app.get("/dev", response_class=HTMLResponse)
def dev():
    return """
    <h1>KRXA DEV</h1>
    <p>파일 생성 / 수정 / 삭제</p>
    <ul>
      <li>main.py</li>
      <li>krxa_engine.py</li>
      <li>krxa_travel.py</li>
    </ul>
    """
