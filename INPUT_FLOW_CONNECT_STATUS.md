# KRXA INPUT FLOW CONNECT STATUS

상태: PASS

추가된 연결:

- samples/m2m/user/input_state.json
- scripts/input_flow.py
- samples/m2m/user/input_result.json 생성
- KRXA_INPUT_FLOW_CONNECT.bat
- run_krxa.py input-flow 명령 연결

흐름:

```text
사용자 입력
→ input_state.json
→ language_db.json 언어 매핑
→ krxai_db.json intent 판단
→ message_state.json 기록
→ session_log.json 누적
→ ROOM_CONNECTED
```

실행:

```bat
KRXA_INPUT_FLOW_CONNECT.bat
python run_krxa.py input-flow
```
