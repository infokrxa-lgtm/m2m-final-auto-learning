from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from pathlib import Path
import html

app = FastAPI(title="KRXA SAFE DEV UI")

SAFE_ROOT = Path(".").resolve()

def safe_path(p: str):
    target = (SAFE_ROOT / p).resolve()
    if not str(target).startswith(str(SAFE_ROOT)):
        raise ValueError("Invalid path")
    return target

@app.get("/")
def home():
    return {"service": "KRXA SAFE DEV UI", "ok": True}

@app.get("/health")
def health():
    return {"ok": True, "version": "SAFE-DEV-RESET"}

@app.get("/ui", response_class=HTMLResponse)
def ui():
    return "<h2>KRXA Voice AI UI</h2><p>Reset OK</p><p><a href='/dev'>DEV FILES</a></p>"

@app.get("/dev", response_class=HTMLResponse)
def dev(path: str = ""):
    root = safe_path(path)

    if root.is_file():
        content = html.escape(root.read_text(encoding="utf-8", errors="ignore"))
        safe_name = html.escape(path)
        return (
            "<html><body>"
            "<h2>KRXA DEV EDIT</h2>"
            f"<p>{safe_name}</p>"
            "<form method='post' action='/dev/save'>"
            f"<input type='hidden' name='path' value='{safe_name}'>"
            f"<textarea name='content' style='width:100%;height:70vh;'>{content}</textarea>"
            "<br><button type='submit'>SAVE</button>"
            "</form>"
            "<p><a href='/dev'>FILE LIST</a></p>"
            "</body></html>"
        )

    items = []
    for item in sorted(root.iterdir()):
        rel = str(item.relative_to(SAFE_ROOT))
        label = html.escape(rel)
        icon = "[DIR]" if item.is_dir() else "[FILE]"
        items.append(f"<li><a href='/dev?path={label}'>{icon} {label}</a></li>")

    return (
        "<html><body>"
        "<h2>KRXA DEV FILES</h2>"
        "<p><a href='/ui'>Voice AI UI</a></p>"
        f"<ul>{''.join(items)}</ul>"
        "</body></html>"
    )

@app.post("/dev/save")
def dev_save(path: str = Form(...), content: str = Form(...)):
    target = safe_path(path)
    target.write_text(content, encoding="utf-8")
    return RedirectResponse(url=f"/dev?path={path}", status_code=303)
