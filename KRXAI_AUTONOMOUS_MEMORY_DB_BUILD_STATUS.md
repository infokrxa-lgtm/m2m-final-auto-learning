# KRXAI AUTONOMOUS MEMORY DB BUILD V22

목표: LLM/ChatGPT 연결이 끊겨도 KRXA 흐름을 유지하는 내부 두뇌 DB.

추가:
- core/krxai_autonomous_memory.json
- core/krxai_task_queue.json
- core/krxai_autorun_policy.json
- krxai_db.json autonomous_mode 확장
- /api/krxai/autonomous/status
- /api/krxai/autonomous/run
- /control 자율 메모리 패널

운영 원칙:
DB 우선 → LLM 보조 → 실패 시 fallback → 기록 → 다음 루프.
