# KRXAI DISCUSSION CORE PATCH V23

## 목적
KRXA_UI <=> KRXAI <=> [KRXAI_DB + language_DB] <=> LLM(필요 시) 구조를 중심 흐름으로 고정한다.

## 핵심
- /api/krxai/discussion/status
- /api/krxai/discussion
- /api/krxai/autonomous/status GET 활성화
- /api/krxai/autonomous/run GET/POST 활성화
- 논의 결과를 core/krxai_autonomous_memory.json 의 discussion_log에 저장

## 원칙
- DB 우선
- KRXAI_DB 중심 판단
- LLM은 필요할 때만 호출
- LLM 실패 시 fallback 유지
