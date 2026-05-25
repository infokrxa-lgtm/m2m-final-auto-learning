# KRXA LLM BRIDGE BUILD V17

## 목적
KRXA HTTPS 실행본에서 KRXAI_DB + language_DB + 파일 교환 manifest + 상태 JSON을 context로 묶고, 필요할 때만 LLM을 호출한다.

## 추가 라우트
- `/krxai` : LLM Bridge Console
- `/api/llm/config` : LLM 설정 조회/저장
- `/api/llm/log` : 호출 로그 조회
- `/api/krxai/ask` : DB 우선 처리 후 필요시 LLM 호출

## Render 환경변수
- `OPENAI_API_KEY` : 실제 호출용 API 키
- `OPENAI_MODEL` : 선택, 기본값 `gpt-5.5`

## 비용 제어
- 기본값은 LLM OFF
- ON일 때도 DB 우선 처리
- unknown intent 또는 사용자가 분석/설계/논의 등을 요청할 때만 호출
