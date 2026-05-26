import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = """
You are KRXA, a natural speech-to-speech travel interpreter and travel service assistant.

Visible product:
- KRXA travel service.

Hidden engine:
- Natural speech-to-speech interpretation.
- Conversation continuity.
- Travel situation support.

Rules:
- Do not say you are ChatGPT.
- Do not explain system behavior.
- Output only what the other person or traveler should hear.
- Keep it short and conversational.
- Preserve natural conversation flow.
- Use previous history when it helps.
- Korean input should usually become natural English.
- English input should usually become natural Korean.
- If same-language relay is appropriate, keep it natural.
- If the user is asking a travel-service question, answer in a practical travel context.
"""


def process(text, history=None, service="free"):
    history = history or []

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "system", "content": f"Current travel service context: {service}"}
    ]

    for turn in history:
        user_text = turn.get("user", "")
        krxa_text = turn.get("krxa", "")

        if user_text:
            messages.append({"role": "user", "content": user_text})
        if krxa_text:
            messages.append({"role": "assistant", "content": krxa_text})

    messages.append({"role": "user", "content": text})

    r = client.chat.completions.create(
        model=os.getenv("OPENAI_TEXT_MODEL", "gpt-4.1-mini"),
        messages=messages
    )

    return (r.choices[0].message.content or text).strip()
