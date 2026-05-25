# KRXA WEB RESEARCH AGENT TRUSTED BUILD V29

## 목표
외부 인터넷 검색을 KRXA에 연결할 준비를 하되, TRUST_GUARD 기준으로 안전 범위와 승인 필요 범위를 분리한다.

## 자유 실행 가능
- 공개 웹페이지 검색 요청
- 일반 정보 요약
- 출처/요약 저장
- KRXAI_DB memory 후보 저장

## 승인 필요
- 비용 발생 API
- 로그인/인증 사이트
- 개인정보/민감정보
- 대량 크롤링/반복 자동 검색
- 저작권 원문 저장
- 외부 게시/배포
- 의료/법률/금융 고위험 판단

## 추가 파일
- core/krxa_web_research_policy.json
- core/krxa_web_research_state.json

## API
- GET /api/krxa/web/status
- POST /api/krxa/web/research

## 주의
V29는 신뢰판별/저장 구조까지 구현한다. 실제 외부 검색 provider 연결은 다음 단계에서 활성화한다.
