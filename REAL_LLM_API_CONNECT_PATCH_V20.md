# KRXA REAL LLM API CONNECT PATCH V20

## 목적
V19에서 UI는 ON으로 보이나 응답 JSON에 `llm_disabled`가 남는 문제를 해결합니다.

## 핵심 수정
- `OPENAI_API_KEY` 환경변수가 있으면 LLM Bridge를 자동 활성화 보정
- 실제 OpenAI Responses API 호출 경로 보강
- `/api/llm/diagnostic` 추가
- 서버 시작 로그에 API KEY SET/NOT_SET, 모델 출력
- `/krxai` 콘솔에 진단 버튼 추가

## Render 설정
Start Command: `python app.py`
Environment:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` = `gpt-4.1`

## 확인 URL
- `/krxai`
- `/api/llm/diagnostic`
