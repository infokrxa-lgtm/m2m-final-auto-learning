from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def process(text):
    r = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "You are a natural travel translator."},
            {"role": "user", "content": text}
        ]
    )
    return r.choices[0].message.content
