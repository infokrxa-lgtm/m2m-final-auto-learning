import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
required = [
    "run_krxa.py",
    "KRXA_RUN.bat",
    "KRXA_RUN_M2M.bat",
    "core/control_state.json",
    "core/session_log.json",
    "core/language_base.json",
    "core/storage_index.json",
    "samples/m2m/user/session_state.json",
    "samples/m2m/user/queue_state.json",
    "samples/m2m/user/presence_state.json",
    "samples/m2m/user/reconnect_state.json",
    "samples/m2m/user/recovery_state.json",
    "samples/m2m/user/message_state.json",
    "samples/m2m/dev/state_machine_spec.json",
    "scripts/state_engine.py",
    "scripts/run_m2m.py",
    "scripts/run_krxa.py",
]

ok = True
for item in required:
    path = ROOT / item
    if not path.exists():
        print(f"MISSING: {item}")
        ok = False
        continue
    if path.suffix == ".json":
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"INVALID JSON: {item} :: {e}")
            ok = False

if ok:
    print("KRXA LOCAL EXEC VERIFY: PASS")
else:
    print("KRXA LOCAL EXEC VERIFY: FAIL")
    raise SystemExit(1)
