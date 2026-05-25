# KRXA LLM CONNECTION ON/OFF CONTROL BUILD V32.7

## 핵심 원칙
KRXA 기본 판단은 내부 KRXAI_DB + 언어DB + MEMORY입니다.
ChatGPT API는 ON/OFF 제어 대상이며, OFF일 때 외부 호출하지 않습니다.

## 추가 API
- GET  /api/llm/config
- GET  /api/llm/status
- POST /api/llm/toggle
  - {"enabled": true}
  - {"enabled": false}

## 응답 필드
- llm_enabled
- llm_used
- llm_reason
- llm_output (ON이고 실제 호출 성공 시)

## UI
/user, /admin, /dev 관제 화면에 LLM 연결 제어 패널 추가.
