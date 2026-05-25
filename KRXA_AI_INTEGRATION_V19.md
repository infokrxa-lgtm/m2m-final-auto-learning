# KRXA AI INTEGRATION V19

이 버전은 다음 3개를 한 번에 묶은 패치입니다.

1. KRXAI 콘솔 연결
2. LLM 자동 호출 정책
3. CONTROL에서 AI 호출

## 기준 흐름

```text
/control 또는 /krxai
→ /api/krxai/ask 또는 /api/control/ai/ask
→ language_db + krxai_db 먼저 조회
→ 부족하면 LLM Bridge 정책 판단
→ OPENAI_API_KEY가 있고 LLM ON이면 API 호출
→ 응답 저장: samples/m2m/user/krxai_console_last.json
→ 호출 기록: core/llm_call_log.json
```

## 주요 URL

```text
/krxai
/control
/api/control/ai
/api/control/ai/ask
/api/krxai/ask
/api/llm/config
/api/llm/log
```

## Render 설정

```text
Start Command: python app.py
Environment Variables:
OPENAI_API_KEY = 실제 키
OPENAI_MODEL = gpt-5.5 또는 사용 모델
```

기본 상태는 안전하게 LLM OFF입니다. /krxai 또는 /control에서 LLM ON으로 바꿔야 실제 호출됩니다.
