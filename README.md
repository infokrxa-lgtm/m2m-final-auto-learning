# KRXA LOCAL BUILD v8 - KRXADB SPLIT

언어_DB와 KRXAI_DB를 분리한 정본입니다.

```text
core/language_db.json  = 언어 재료
core/krxai_db.json     = 판단/의도/흐름
core/db_index.json     = DB 호출 순서
```

실행:

```bat
KRXA_DB_PROBE.bat
KRXA_RUN_M2M.bat
KRXA_OPEN_CONTROL_UI.bat
KRXA_OPEN_USER_UI.bat
```

---

# KRXA LOCAL BUILD v3 CANON

이 폴더가 현재 정본입니다.

## 의미

- v1: 기본 골격
- v2: 실행 엔진
- v3_CANON: 기본 골격 + 실행 엔진 + 정본 기준판

앞으로 작업은 이 폴더 하나에서만 진행합니다.

## 실행

```bat
python run_krxa.py status
python run_krxa.py run-m2m
python run_krxa.py recover
python run_krxa.py reset
```

또는:

```bat
KRXA_RUN.bat
KRXA_RUN_M2M.bat
KRXA_RESET.bat
```

## 핵심 구조

```text
core/
samples/m2m/user/
samples/m2m/dev/
samples/m2m/verify/
scripts/
build/
run_krxa.py
```

## 원칙

내 컴퓨터에서 완성하고, 저장소에는 완성본을 올린다.
Google Drive는 제작소가 아니라 업로드/보관소다.


## v6 USER UI

사용자 입력 화면 실행:

```bat
KRXA_OPEN_USER_UI.bat
```

생성 결과는 `message_state.json`으로 저장해 `samples/m2m/user/message_state.json`에 반영할 수 있습니다.


## v9 INPUT FLOW CONNECT

사용자 입력을 KRXADB에 연결합니다.

```bat
KRXA_INPUT_FLOW_CONNECT.bat
python run_krxa.py input-flow
```

입력 파일:

```text
samples/m2m/user/input_state.json
```

출력 파일:

```text
samples/m2m/user/input_result.json
samples/m2m/user/message_state.json
core/session_log.json
```


## v12 HTTPS REALTIME DEPLOY

HTTPS 실시간 배포 준비판입니다. Render 기준으로 `render.yaml`, `Procfile`, `requirements.txt`가 포함됩니다.

로컬 실행:
```bat
KRXA_HTTPS_REALTIME_LOCAL.bat
```

웹 배포 후 사용자 UI:
```text
https://<service-url>/samples/m2m/user/multi_user_ui.html
```


## KRXA v13 FULL WEB SERVER WRAP

Render start command:

```text
python app.py
```

Local test:

```bat
KRXA_WEB_SERVER_LOCAL.bat
```

URLs after Render deploy:

```text
https://krxa.onrender.com/
https://krxa.onrender.com/user
https://krxa.onrender.com/multi
https://krxa.onrender.com/control
https://krxa.onrender.com/api/health
```


## V20 REAL LLM API CONNECT PATCH
- LLM 실제 호출 연결 보정
- /api/llm/diagnostic 추가
- Render ENV 기반 자동 활성화
