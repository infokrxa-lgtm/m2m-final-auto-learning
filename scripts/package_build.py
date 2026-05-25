from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "build" / "KRXA_LOCAL_BUILD_EXEC_v2.zip"
OUT.parent.mkdir(exist_ok=True)

with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
    for p in ROOT.rglob("*"):
        if p.is_file() and p != OUT and "__pycache__" not in p.parts:
            z.write(p, p.relative_to(ROOT))

print(f"PACKAGED: {OUT}")
