# KRXA V33.7.1 BILLING UX CONTROL FULL

- 무료 종료 시 차단이 아닌 연장 되묻기 UX
- 말대말 통제에서 AI 과금 ON/OFF 설정
- ON: 무료 10분 + 유료 10/20/30분
- OFF: 무료 모드만 유지
- ChatGPT 우선 구조 유지
- 자연 대화 흐름 우선

UI:
- /m2m-billing-control
- /m2m/billing-control

API:
- GET  /api/m2m/billing/status
- GET  /api/m2m/billing/config
- POST /api/m2m/billing/config
- POST /api/m2m/billing/session/start
- POST /api/m2m/billing/extend-prompt
- POST /api/m2m/billing/reset
