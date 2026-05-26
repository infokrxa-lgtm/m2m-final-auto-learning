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
    <h1>KRXA USER</h1>
    <p>여행 서비스 UI</p>
    <a href="/app?service=food">맛집</a><br>
    <a href="/app?service=map">길찾기</a><br>
    <a href="/app?service=hotel">숙소</a><br>
    """

# ---------------- APP ----------------
@app.get("/app", response_class=HTMLResponse)
def app_ui(service: str = "free"):
    return f"""
    <h1>서비스 실행: {service}</h1>

    <textarea id="t"></textarea><br>
    <button onclick="send()">전송</button>

    <div id="out"></div>

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

    document.getElementById("out").innerHTML += "<p>"+j.result+"</p>";

    if(j.cards){
        j.cards.forEach(c=>{
            if(c.url){
                document.getElementById("out").innerHTML +=
                    "<a href='"+c.url+"' target='_blank'>"+c.label+"</a><br>";
            }else{
                document.getElementById("out").innerHTML +=
                    "<p>"+c.text+"</p>";
            }
        });
    }
}
</script>

        document.getElementById("out").innerHTML += "<p>"+j.result+"</p>";
    }}
    </script>

    <br><a href="/user">← 돌아가기</a>
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
