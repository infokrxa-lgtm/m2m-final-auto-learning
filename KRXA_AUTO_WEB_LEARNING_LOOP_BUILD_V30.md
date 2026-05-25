# KRXA AUTO WEB LEARNING LOOP BUILD V30

## 원칙
사용자 요청 사안에 한정한다.

## 동작
USER_QUERY → TRUST_GUARD_CHECK → SAFE_FETCH → SUMMARY_EXTRACT → SOURCE_STORE → MEMORY_CANDIDATE_STORE → FOLLOWUP_SUGGESTIONS

## 제한
- 자동 반복 없음
- 사용자 요청 없는 검색 없음
- 원문 전문 저장 없음
- 대량 크롤링 없음
- 로그인/유료/민감정보는 승인 대기

## API
- GET /api/krxa/web/learning/status
- POST /api/krxa/web/learning/run

## POST 예시
{
  "query": "삼성전자 최근 뉴스 요약"
}
