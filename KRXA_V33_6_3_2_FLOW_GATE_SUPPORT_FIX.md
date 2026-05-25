# KRXA V33.6.3.2 FLOW GATE SUPPORT FIX

## 수정
- 저장된 테스트 usage/log 파일 제거
- 마이크/스피커/기기/시간/날짜/날씨 질문은 무료 내부 지원으로 처리
- 유료 게이트 전에 무료 지원 응답
- 유료 안내 반복 문구 개선
- 사용량 리셋 API 추가

## 추가 API
POST /api/m2m/ai/usage/reset
body: {"user_id":"default"}

## 테스트
- 지금 몇 시야?
- 오늘 며칠이야?
- 마이크를 바꿔야 하나?
- 안녕
