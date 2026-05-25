# KRXA HTTPS REALTIME DEPLOY v12

목표: 로컬 멀티유저 엔진을 HTTPS 웹 서버에서 실행 가능한 구조로 전환.

## 배포 대상
- Render / Railway / Fly.io 같은 Python Web Service
- GitHub Pages 단독 배포는 API 서버가 없어서 실시간 엔진 실행 불가

## 실행 URL 예시
- /samples/m2m/user/multi_user_ui.html
- /api/state
- /api/send

## 상태
- multi_user_engine.py: HOST/PORT 환경변수 지원
- Procfile 추가
- render.yaml 추가
- requirements.txt 추가
