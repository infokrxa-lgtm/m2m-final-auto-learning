# KRXA V31.1 RUNTIME FIX

Fixes HTTP 502 runtime errors after V31 deploy.

## Fixes
- BASE_DIR undefined -> set BASE_DIR = ROOT
- urllib.parse missing import
- _send_html missing method for /window/* routes
- report/file/memory paths normalized to ROOT

## Verify
- /api/memory/user?user_id=default
- /api/files/reports
- /window/krxai
- /api/tasks/auto/status
