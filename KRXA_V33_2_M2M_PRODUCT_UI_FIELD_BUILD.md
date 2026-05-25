# KRXA V33.2 M2M PRODUCT UI FIELD BUILD

## 기준
- V33.1 KRXA 엔진 유지
- 새 필드: 말대말 제품 UI 확장판

## 추가 경로
- /m2m-product
- /m2m
- /api/m2m/status
- /api/llm/execute

## 추가 기능
- 말대말 제품 UI
- 음성인식 버튼(Web Speech API)
- 복수창: 사용자 / 관제 / 개발 / 말대말
- LLM 강제 실행 라우팅
- "LLM 실행:" 명령은 KRXAI 답변층을 건너뛰고 실제 LLM으로 직접 라우팅

## 배포
```bat
git add .
git commit -m "V33.2 M2M PRODUCT UI FIELD BUILD"
git push -u origin main --force
```

## 확인
- https://서비스주소/m2m-product
- https://서비스주소/api/m2m/status
- https://서비스주소/api/llm/execute
