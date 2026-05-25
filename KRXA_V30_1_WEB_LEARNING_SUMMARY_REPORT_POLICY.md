# KRXA V30.1 WEB LEARNING SUMMARY + REPORT POLICY

## 사용자 조건 반영

1. 검색/분석 수행 시
- 고리형 학습 기억 루프에는 전체 검색 결과를 저장하지 않는다.
- 시발점 요약(seed summary)만 저장한다.
- 저장 항목: query, purpose, trust_decision, seed_summary, source_count, top_source_titles, followup_suggestions.

2. 보고서/리포트 요청 시
- 현실 의사결정에 쓸 수 있는 최고 보고서 수준으로 구성한다.
- Executive Summary, 목적/범위, 핵심 발견, 근거/출처, 분석, 리스크, 실행 전략, 다음 액션을 포함한다.
- 보고서 전문은 memory_loop에 그대로 저장하지 않고 시발점 요약과 핵심 결론만 저장한다.

## 확인 API
- /api/db/auto_web_learning_policy
- /api/db/report_quality_policy
- POST /api/krxa/web/learning/run
