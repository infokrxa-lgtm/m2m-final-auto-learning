# KRXA V33.6.1 ROUTING GUARD PATCH

## 목적
어제처럼 KRXAI가 최종 답변해버리는 문제를 차단합니다.

## 구조
USER → KRXA ROUTER → 언어DB/KRXAI 판단 → LLM 필요 시 LLM 호출 → 결과 저장 → UI 출력

## 정책
- KRXAI = 판단/기억/보조
- LLM = 최종 생성/분석/설계/전략 답변
- 모호한 요청은 KRXAI 답변 금지, LLM으로 라우팅

## API
- GET /api/krxa/router/status
- POST /api/krxa/router/run
- GET /api/m2m/router/status
- POST /api/m2m/router/run
