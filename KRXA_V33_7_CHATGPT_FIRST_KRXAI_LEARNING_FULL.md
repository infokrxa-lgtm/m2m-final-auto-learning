# KRXA V33.7 CHATGPT FIRST + KRXAI LEARNING FULL

## 확정 원칙
1. KRXA router 조건 제거
2. 무조건 ChatGPT 먼저 호출
3. KRXA 초청문 자동 삽입
4. history 유지
5. KRXAI는 공부/학습 데이터 적재 담당
6. 과금/사용량은 응답 후 관리

## 핵심 흐름
사용자 입력
→ ChatGPT 100% 우선 호출
→ 자연 대화 응답
→ history 저장
→ krxai_training_log.json 저장
→ KRXA 사용량/과금 상태 후처리

## API
- POST /api/v337/chat
- GET /api/v337/status
- POST /api/krxa/chatgpt-first/run
- GET /api/krxa/chatgpt-first/status

## 저장 파일
- core/krxa_chatgpt_first_history.json
- core/krxai_training_log.json

## Render ENV
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-4.1-mini
