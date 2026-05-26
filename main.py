from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from krxa_engine import process
from krxa_travel import get_cards

app = FastAPI()


@app.post("/chat")
def chat(text: str = Form(...), service: str = Form("free")):
    result = process(text)
    cards = get_cards(text, service)
    return {
        "result": result,
        "cards": cards
    }


@app.get("/")
def root():
    return {"ok": True, "version": "V60-STEP3"}


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
    return f"""
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:Arial;background:#eef2f7;margin:0}}
.wrap{{max-width:520px;margin:auto;min-height:100vh;background:white;padding:20px;box-sizing:border-box}}
h1{{font-size:28px}}
textarea{{width:100%;height:90px;box-sizing:border-box;border-radius:12px;padding:12px;font-size:16px}}
button{{padding:10px 16px;border:0;border-radius:10px;background:#2563eb;color:white;font-weight:bold;margin-top:8px}}
.msg{{padding:12px;margin:10px 0;border-radius:12px}}
.me{{background:#dbeafe}}
.krxa{{background:#f3f4f6}}
.card{{padding:12px;margin:8px 0;border-radius:12px;background:#fff7ed;border:1px solid #fed7aa}}
a{{color:#2563eb;font-weight:bold}}
</style>
</head>

<body>
<div class="wrap">
<h1>{service} 서비스</h1>

<textarea id="t" placeholder="사용자 입력 언어로 입력하세요"></textarea><br>
<button onclick="send()">전송</button>

<div id="chat"></div>
<div id="cards"></div>

<br><a href="/user">← 사용자 화면으로 돌아가기</a>
</div>

<script>
async function send(){{
    let input = document.getElementById("t");
    let text = input.value.trim();

    if(!text){{
        alert("내용을 입력하세요.");
        return;
    }}

    input.value = "";

    let fd = new FormData();
    fd.append("text", text);
    fd.append("service", "{service}");

    let r = await fetch("/chat", {{
        method: "POST",
        body: fd
    }});

    let j = await r.json();

    let chat = document.getElementById("chat");
    chat.innerHTML += "<div class='msg me'><b>나:</b> " + text + "</div>";
    chat.innerHTML += "<div class='msg krxa'><b>KRXA:</b> " + j.result + "</div>";

    let html = "";
    if(j.cards){{
        j.cards.forEach(function(c){{
            if(c.url){{
                html += "<div class='card'><a href='" + c.url + "' target='_blank'>" + c.label + "</a></div>";
            }} else {{
                html += "<div class='card'>" + c.text + "</div>";
            }}
        }});
    }}

    document.getElementById("cards").innerHTML = html;
}}
</script>
</body>
</html>
"""


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
