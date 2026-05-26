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
    page = """
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{margin:0;font-family:Arial;background:#eef2f7}
.wrap{max-width:480px;margin:auto;height:100vh;display:flex;flex-direction:column}
.header{background:white;padding:15px;font-weight:bold;border-bottom:1px solid #ddd}
.chat{flex:1;overflow:auto;padding:10px}
.msg{padding:10px;border-radius:12px;margin:8px 0;max-width:80%}
.me{background:#dbeafe;margin-left:auto}
.bot{background:white;border:1px solid #ddd}
.input{padding:10px;background:white;border-top:1px solid #ddd}
textarea{width:100%;border-radius:10px;padding:10px}
button{margin-top:5px;padding:10px;width:100%;border:none;border-radius:10px;background:#2563eb;color:white;font-weight:bold}
.card{background:#fff;padding:10px;border-radius:10px;margin:5px 0;border:1px solid #ddd}
</style>
</head>
<body>
<div class="wrap">
  <div class="header">__SERVICE__ 서비스</div>

  <div id="chat" class="chat"></div>
  <div id="cards"></div>

  <div class="input">
    <textarea id="t" placeholder="말하거나 입력하세요"></textarea>
    <button onclick="send()">전송</button>
  </div>
</div>

<script>
async function send(){
 let text = document.getElementById("t").value;

 let fd = new FormData();
 fd.append("text", text);

 let r = await fetch("/chat", {
  method:"POST",
  body:fd
 });

 let j = await r.json();

 let chat = document.getElementById("chat");
 chat.innerHTML += "<div class='msg me'>"+text+"</div>";
 chat.innerHTML += "<div class='msg bot'>"+j.result+"</div>";

 let cardsDiv = document.getElementById("cards");
 cardsDiv.innerHTML = "";

 if(j.cards){
  j.cards.forEach(function(c){
   if(c.url){
    cardsDiv.innerHTML += "<div class='card'><a href='"+c.url+"' target='_blank'>"+c.label+"</a></div>";
   }else{
    cardsDiv.innerHTML += "<div class='card'>"+c.text+"</div>";
   }
  });
 }

 chat.scrollTop = chat.scrollHeight;
}
</script>
</body>
</html>
"""
    return page.replace("__SERVICE__", service)
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
