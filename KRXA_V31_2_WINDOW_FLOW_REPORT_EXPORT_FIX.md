# KRXA V31.2 WINDOW FLOW + REPORT EXPORT FIX

## 수정
1. CONTROL의 독립화면 링크를 /window/* 로 활성화
2. CONTROL KRXAI 논의창에서 보고서/검색/분석 요청 시 /api/krxa/web/learning/run으로 연결
3. 보고서 실행 후 FILE/MEMORY/TASK 창 갱신
4. 보고서 export 포맷을 JSON/TXT/DOCX/PDF로 확장
5. FILE_EXCHANGE manifest에 생성 파일 등록 및 다운로드 링크 제공
6. /window/* 독립 화면별 API 실행 로직 강화

## 확인
- /control
- /window/krxai
- /window/file
- POST /api/krxa/web/learning/run {"query":"삼성전자 전략 보고서","user_id":"default"}
- /api/files/reports
- /api/files/download/{filename}
