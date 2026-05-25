import os
import json
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel
from openai import OpenAI

app = FastAPI(title="KRXA V34 SP VOICE AI")
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

DATA_DIR = Path("storage")
DATA_DIR.mkdir(exist_ok=True)
HISTORY_FILE = DATA_DIR / "history.json"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini")
STT_MODEL = os.getenv("OPENAI_STT_MODEL", "whisper-1")
TTS_MODEL = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts")

INVITE_PROMPT = """
[KRXA V34.4 SP-VOICE-AI]

V34.1 = STT voice input
V34.2 = streaming response
V34.3 = 13-language auto interpretation
V34.4 = memory loop

Core rule:
KRXA does not judge first.
KRXA always calls ChatGPT first.

Trigger:
- "첨부파일" means load context.
- "여기서부터 통역시작하자" means interpretation mode ON.

Supported 13 languages:
ko, en, ja, zh, es, fr, de, vi, th, id, ar, ru, pt

Behavior:
- Detect input language automatically.
- Translate naturally when interpretation mode is active.
- Preserve conversation flow.
- Use previous history.
- Answer clearly and briefly.
"""


class ChatRequest(BaseModel):
    text: str


def load_history():
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except Exception:
        return []


def save_history(user_text, assistant_text):
    history = load_history()
    history.append({"user": user_text, "assistant": assistant_text})
    HISTORY_FILE.write_text(
        json.dumps(history[-50:], ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def build_messages(user_text):
    history = load_history()[-10:]

    messages = [{"role": "system", "content": INVITE_PROMPT}]

    for item in history:
        messages.append({"role": "user", "content": item.get("user", "")})
        messages.append({"role": "assistant", "content": item.get("assistant", "")})

    messages.append({"role": "user", "content": user_text})
    return messages


@app.get("/")
def home():
    return {"service": "KRXA V34 SP VOICE AI", "ok": True}


@app.get("/health")
def health():
    return {"ok": True, "version": "V34.4-SP-VOICE-AI"}


@app.post("/chat")
def chat(req: ChatRequest):
    response = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=build_messages(req.text),
    )

    answer = response.choices[0].message.content or ""
    save_history(req.text, answer)

    return {
        "ok": True,
        "input": req.text,
        "response": answer,
    }


@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    def event_stream():
        full_text = ""

        stream = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=build_messages(req.text),
            stream=True,
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                full_text += delta
                yield f"data: {json.dumps({'delta': delta}, ensure_ascii=False)}\n\n"

        save_history(req.text, full_text)
        yield f"data: {json.dumps({'done': True}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/stt")
async def stt(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=audio_file,
            )

        return {
            "ok": True,
            "text": transcript.text,
        }
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.post("/voice")
async def voice(file: UploadFile = File(...)):
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"

    with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model=STT_MODEL,
                file=audio_file,
            )

        user_text = transcript.text

        response = client.chat.completions.create(
            model=TEXT_MODEL,
            messages=build_messages(user_text),
        )

        answer = response.choices[0].message.content or ""
        save_history(user_text, answer)

        return {
            "ok": True,
            "text": user_text,
            "response": answer,
        }
    finally:
        try:
            os.remove(tmp_path)
        except Exception:
            pass


@app.post("/tts")
def tts(req: ChatRequest):
    audio = client.audio.speech.create(
        model=TTS_MODEL,
        voice="coral",
        input=req.text,
    )

    return Response(
        content=audio.read(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"},
    )


@app.get("/history")
def history():
    return {"ok": True, "history": load_history()}
