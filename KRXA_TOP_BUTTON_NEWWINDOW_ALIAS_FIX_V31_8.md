# KRXA TOP BUTTON NEWWINDOW ALIAS FIX V31.8

## Fix
- HTS/CONTROL 상단 KRXAI/DB/MEMORY/TASK/FILE/API LOG 버튼 클릭 시 새 브라우저 업무창 오픈
- /HTS 대문자, /hts, /desktop 모두 지원
- /api/autonomous/tick 및 /api/tasks/auto/tick alias 보강
- /api/files/reports safe response 보강

## 확인
- /HTS
- 상단 KRXAI 버튼 클릭 -> /window/krxai 새창
- 상단 DB 버튼 클릭 -> /window/db 새창
- CMD: curl -X POST https://krxa.onrender.com/api/autonomous/tick ...
