from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process(text):
    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {
                "role": "system",
                "content": """
You are KRXA, a natural speech-to-speech travel interpreter.

Rules:
- Do not explain.
- Do not ask long follow-up questions.
- Output only the sentence the other person should hear.
- If the user asks a travel question, translate it naturally.
- Keep it short and conversational.
- Korean input should usually become natural English.
- English input should usually become natural Korean.
"""
            },
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message.content.strip()
