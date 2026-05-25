# KRXA LLM FORCE / AUTO MODE CONTROL BUILD V32.8

## LLM 모드
- OFF: 외부 ChatGPT API 호출 금지
- AUTO: 내부 판단 우선, 필요할 때만 호출
- FORCE: 사용자가 요청하면 무조건 호출

## API
- GET  /api/llm/mode
- POST /api/llm/mode
  - {"mode":"off"}
  - {"mode":"auto"}
  - {"mode":"force"}

기존:
- GET /api/llm/config
- POST /api/llm/toggle

## 응답 필드
- llm_mode
- force_llm
- llm_enabled
- llm_used
- llm_reason
- llm_output
