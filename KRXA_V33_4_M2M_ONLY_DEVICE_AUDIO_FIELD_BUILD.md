# KRXA V33.4 M2M ONLY DEVICE AUDIO FIELD BUILD

## 기준
- Render 데이터량을 줄이기 위해 일단 말대말만 구축합니다.
- KRXA 통합관제는 나중에 API로 연결합니다.
- m2m-final-auto-learning 서비스에서 말대말 사용자/관제/개발 UI를 제공합니다.

## 경로
- /user : 말대말 사용자 통합창
- /m2m-product : 말대말 사용자 통합창
- /m2m-control : 말대말 관제창
- /m2m-dev : 말대말 개발자 UI
- /m2m/editor : 파일/동영상 새창 편집기
- /api/m2m/status : 상태 확인

## 추가 기능
- 사용자 기기 마이크 자동 인식
- 사용자 기기 스피커 자동 인식
- 음성 입력(Web Speech API)
- 음성 출력(SpeechSynthesis API)
- 파일/동영상 선택 및 새창 편집
- 복수창 운영
- KRXA API 연결 자리만 유지
