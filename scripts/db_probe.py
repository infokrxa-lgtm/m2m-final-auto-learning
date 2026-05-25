import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_json(rel):
    with open(ROOT / rel, 'r', encoding='utf-8') as f:
        return json.load(f)

def probe(text='안녕하세요'):
    language = load_json('core/language_db.json')
    ai = load_json('core/krxai_db.json')
    pairs = language.get('translation_pairs', [])
    translated = next((p['target'] for p in pairs if p.get('source') == text), text)
    intent = ai.get('confidence_rules', {}).get('fallback_intent', 'm2m_message')
    for name, rule in ai.get('intents', {}).items():
        pats = rule.get('patterns', [])
        if any(p != '*' and p.lower() in text.lower() for p in pats):
            intent = name
            break
    print('KRXADB PROBE: PASS')
    print(f'INPUT: {text}')
    print(f'INTENT: {intent}')
    print(f'OUTPUT: {translated}')

if __name__ == '__main__':
    probe()
