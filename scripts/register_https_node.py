from __future__ import annotations
import json, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
INDEX = ROOT / "core" / "storage_index.json"

def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/register_https_node.py <HTTPS_URL>")
        raise SystemExit(2)
    url = sys.argv[1].strip()
    if not (url.startswith("https://")):
        print("ERROR: URL must start with https://")
        raise SystemExit(1)
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    data.setdefault("nodes", {}).setdefault("https_release", {})
    data["nodes"]["https_release"].update({
        "type": "https",
        "role": "portable_release_node",
        "url": url,
        "status": "registered",
        "artifact": "build/KRXA_RELEASE.zip"
    })
    INDEX.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print("KRXA HTTPS NODE REGISTER: PASS")
    print("URL:", url)

if __name__ == "__main__":
    main()
