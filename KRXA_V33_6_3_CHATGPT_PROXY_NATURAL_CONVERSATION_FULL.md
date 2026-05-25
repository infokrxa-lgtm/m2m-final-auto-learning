# KRXA V33.6.3 CHATGPT PROXY NATURAL CONVERSATION FULL

반영:
- ChatGPT Proxy 우선 라우팅
- KRXAI/언어DB 최종 출력 차단
- 초청문 자동 삽입
- 무료 5분 안내
- 추가 사용 동의
- 10분/30분/1시간 정책
- 종료 1분 전 안내
- 종료 시점 재안내
- 자동 연장 금지

API:
- GET /api/m2m/ai/usage/status
- POST /api/m2m/ai/session/start
- POST /api/m2m/ai/session/stop
- POST /api/m2m/chatgpt/proxy/run

Render ENV:
- OPENAI_API_KEY=...
- OPENAI_MODEL=gpt-4.1-mini
