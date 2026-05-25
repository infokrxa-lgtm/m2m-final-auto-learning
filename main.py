from fastapi import FastAPI

app = FastAPI(title="KRXA V34 SP VOICE AI")

@app.get("/")
def home():
    return {"service": "KRXA V34 SP VOICE AI", "ok": True}

@app.get("/health")
def health():
    return {"ok": True, "version": "V34.0-SP-VOICE-AI"}
