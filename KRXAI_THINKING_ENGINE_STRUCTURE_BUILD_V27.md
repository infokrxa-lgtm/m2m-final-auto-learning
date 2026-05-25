# KRXAI THINKING ENGINE STRUCTURE BUILD V27

## 목표
KRXAI를 단순 응답 시스템이 아닌 ROOT 기반 판단 + MEMORY 기반 학습 + LOOP 기반 진화 구조로 재구성한다.

## 핵심 파일
- core/krxai_root.json
- core/krxai_memory_index.json
- core/krxai_thinking_engine.json
- core/krxai_core_memory.json

## 동작 순서
ROOT_LOAD → MEMORY_RETRIEVE → CONTEXT_COMPARE → JUDGEMENT_CREATE → STRUCTURED_RESPONSE → LOOP_STORE

## 응답 구조
{
  "reason": "판단 근거",
  "memory_used": "참조된 기억",
  "final": "최종 응답"
}

## LLM 정책
외부 LLM 사용하지 않음. 내부 DB 기반 사고 엔진만 사용.

## 확인
- /api/krxai/thinking/status
- /api/krxai/thinking
- /krxai

## 테스트
- KRXA 시발점이 뭐야?
- 고리형 학습 구조 설명해
- 프랙탈 구조가 뭐야?
- 신뢰붕괴방지 원칙은?
