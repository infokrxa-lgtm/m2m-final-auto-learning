# KRXA FULL SYSTEM REBUILD V18

V18은 V16 통합관제센터 설계와 V17 LLM Bridge, V15 File Exchange, V14 KRXAI Console, V13 HTTPS Web Server를 하나로 재조립한 정본입니다.

## 핵심
- `/control` 중심 통합관제
- `/api/control/status` 통합 상태 API
- `core/principles.json` 등 핵심 원칙 파일 실장
- KRXAI_DB + language_DB + LLM Bridge + 파일교환 + 멀티유저 상태 통합
- Render Start Command: `python app.py`

## 배포
```bat
git init
git branch -M main
git add .
git commit -m "KRXA v18 FULL SYSTEM REBUILD"
git remote add origin https://github.com/infokrxa-lgtm/KRXA.git
git push -u origin main --force
```

Render 설정은 유지:

```text
Start Command: python app.py
```

## 접속
- https://krxa.onrender.com/control
- https://krxa.onrender.com/krxai
- https://krxa.onrender.com/files
- https://krxa.onrender.com/multi

Generated: 2026-05-21T15:50:47.181710+00:00
