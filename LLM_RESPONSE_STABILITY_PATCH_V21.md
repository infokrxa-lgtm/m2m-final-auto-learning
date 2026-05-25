# KRXA V21 LLM RESPONSE STABILITY PATCH

## 목적
- 연속 LLM 호출 중 단순 `ERROR`만 표시되는 문제를 줄인다.
- OpenAI HTTP 오류, URL 오류, 빈 응답 오류를 `LLM_ERROR: ...` 형태로 노출한다.
- `/krxai` 화면이 `ok:false` 응답에서 무조건 예외 처리로 끊기지 않도록 조정한다.

## 핵심 변경
- `app.py`
  - OpenAI HTTPError 상세 메시지 표시
  - 빈 응답 감지
  - LLM 실패 시 DB fallback과 상세 error 기록
- `admin/krxai_console.html`
  - JSON 응답 전체 표시 안정화

## 확인 주소
- `/krxai`
- `/api/llm/diagnostic`
