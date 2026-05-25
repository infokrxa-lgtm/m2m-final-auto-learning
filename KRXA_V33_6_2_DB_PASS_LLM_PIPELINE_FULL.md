# KRXA V33.6.2 DB PASS + LLM PIPELINE FULL

## 핵심 수정
- language_db는 최종 화면 출력이 아니라 참고 자료로만 사용
- KRXAI는 판단/기억/보조 역할만 수행
- 복잡/모호/보고서/문장구조/설계/분석 요청은 LLM 최종 응답으로 라우팅
- 단순 인사/상태/파일목록 등만 내부 처리

## 작동 흐름
USER → KRXA ROUTER → languageDB/KRXAI reference → LLM if needed → MEMORY → UI

## 테스트
- `안녕하세요` → 내부 간단 응답
- `문장 구조에 대해 설명해줘` → LLM 호출
- `삼성전자 전략 보고서 작성` → LLM 호출
- `/api/krxa/router/status_v3362` → 라우터 상태
