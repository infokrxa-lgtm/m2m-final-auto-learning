# KRXA FULL SYSTEM ADVANCED OPERATION BUILD V31

## 포함
1. Multi User Memory Isolation
2. Auto Task Execution Engine
3. Window Based UI Execution System
4. Report File Export System

## 주요 API
- GET /api/memory/user?user_id=default
- GET /api/tasks/auto/status
- POST /api/tasks/auto/tick
- POST /api/report/export
- GET /api/files/reports
- GET /api/files/download/{filename}
- GET /window/krxai
- GET /window/memory
- GET /window/task
- GET /window/file

## 보고서 파일
- files/reports/report_{user_id}_{timestamp}.json
- files/reports/report_{user_id}_{timestamp}.txt

## 정책
보고서 전문은 파일로 저장하고, memory에는 시발점 요약 및 파일명만 저장한다.
