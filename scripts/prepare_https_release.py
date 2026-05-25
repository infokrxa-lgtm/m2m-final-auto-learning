from __future__ import annotations
import hashlib, json, pathlib, zipfile, datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
BUILD = ROOT / "build"
RELEASE = BUILD / "KRXA_RELEASE.zip"
EXCLUDE = {"build/KRXA_RELEASE.zip", "build/HTTPS_RELEASE_MANIFEST.json"}

def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def main() -> None:
    BUILD.mkdir(exist_ok=True)
    files = []
    with zipfile.ZipFile(RELEASE, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(ROOT.rglob("*")):
            if not p.is_file():
                continue
            rel = p.relative_to(ROOT).as_posix()
            if rel in EXCLUDE or rel.endswith(".zip"):
                continue
            z.write(p, rel)
            files.append(rel)
    manifest = {
        "schema": "krxa.https_release_manifest.v1",
        "artifact": "build/KRXA_RELEASE.zip",
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "sha256": sha256(RELEASE),
        "files_count": len(files),
        "files": files,
        "next_step": "Upload build/KRXA_RELEASE.zip to an HTTPS-accessible storage, then paste the URL into core/storage_index.json"
    }
    (BUILD / "HTTPS_RELEASE_MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("KRXA HTTPS RELEASE PREPARE: PASS")
    print("ARTIFACT:", RELEASE)
    print("SHA256:", manifest["sha256"])

if __name__ == "__main__":
    main()
