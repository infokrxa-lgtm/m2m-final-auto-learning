# KRXA WINDOW WORKSPACE UI OPERATION BUILD V31.5

## 목표
KRXA / DB / MEMORY / TASK / FILE / API LOG 각 버튼이 독립 업무창을 열고,
각 창에서 해당 업무를 조회/생성/수정/저장/삭제/실행할 수 있도록 한다.

## 창
- /window/krxai
- /window/db
- /window/memory
- /window/task
- /window/file
- /window/apilog

## API
- POST /api/memory/add
- POST /api/memory/delete
- POST /api/tasks/add
- POST /api/tasks/delete
- GET /api/apilog
- 기존 /api/db/save, /api/files/delete, /api/files/reports 유지
