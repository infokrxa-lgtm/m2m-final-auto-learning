# KRXAI CORE MEMORY SEED BUILD V2 - V28

## 목표
자동 학습 + 성격 형성 모드.

## 추가 파일
- core/krxai_personality_profile.json
- core/krxai_auto_learning_policy.json
- core/krxai_core_memory_seed_v2.json

## 핵심
- 반복 입력 태그를 learning_counters에 반영
- memory_index에 core seed를 사전 주입
- 응답에 personality / auto_learning 상태 포함
- 외부 LLM 없이 내부 DB 기반 사고 유지

## 확인
- /api/krxai/thinking/status
- /api/db/krxai_personality_profile
- /api/db/krxai_auto_learning_policy
- /api/db/krxai_core_memory_seed_v2
- /krxai
