from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi import Form
from krxa_engine import process


app = FastAPI()
@app.post("/chat")
def chat(text: str = Form(...)):
    result = process(text)
    return {"result": result}
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
    <p>여기서 대화 + 통역 + 서비스 결합</p>
    <a href="/user">← 돌아가기</a>
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
