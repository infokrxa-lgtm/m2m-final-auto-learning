# KRXA WINDOW API FLOW CONNECT BUILD V25

목표: `/control`을 바탕화면형 운영 UI로 두고, 각 WINDOW가 실제 API를 호출하여 DB/메모리/작업/파일/방/신뢰/KRXAI 내부 엔진과 연결되도록 한다.

## 연결 구조

```text
CONTROL DESKTOP
├─ KRXAI_WINDOW  → POST /api/krxai/discussion
├─ DB_WINDOW     → GET/POST /api/db/{krxai_db|language_db|db_index}
├─ MEMORY_WINDOW → GET /api/memory, POST /api/krxai/autonomous/run
├─ TASK_WINDOW   → GET /api/tasks, POST /api/tasks/add
├─ FILE_WINDOW   → GET /api/files, POST /api/files/upload
├─ ROOM_WINDOW   → GET /api/state, POST /api/send
├─ TRUST_WINDOW  → GET /api/control/trust
├─ ADMIN_WINDOW  → GET /api/platform/status
└─ DEV_WINDOW    → GET /api/health, GET /api/control/db
```

## 원칙

- 외부 LLM 필수 아님.
- KRXAI_DB + language_DB + memory_loop + task_queue 중심.
- 각 WINDOW는 독립 화면 링크와 내부 API 작동 버튼을 동시에 가진다.
- 버튼 클릭 시 Render Logs에 실제 `/api/...` 요청이 남아야 정상이다.
