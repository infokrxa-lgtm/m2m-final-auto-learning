# KRXA V31.4 USER OPERABLE FILE REPORT MANAGER FIX

## 반영
- 내부 DB/프로그램 JSON 수정·저장 화면: /window/db
- 보고서 파일 관리자 화면: /window/file 또는 /files
- 보고서 리스트 클릭 다운로드
- 보고서 삭제 관리
- DOCX/PDF/TXT/JSON 생성 유지
- PDF 한글 CID 폰트 적용: HYSMyeongJo-Medium
- CONTROL 독립화면 링크 /window/* 연결

## 확인
- /window/krxai
- /window/file
- /window/db
- /api/files/reports
- /api/files/download/{filename}
- POST /api/files/delete
- POST /api/db/save
