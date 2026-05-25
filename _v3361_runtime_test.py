
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_1_KRXA_ROUTING_GUARD_PATCH/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.krxa_v3361_router_classify('삼성전자 전략 분석 보고서 작성')['llm_required']
assert not m.krxa_v3361_router_classify('파일 목록 조회')['llm_required']
assert m.krxa_v3361_router_classify('무엇을 해야 하지')['reason']=='unknown_intent_guard_prevents_krxai_fake_answer'
assert m.krxa_v3361_router_status()['policy']['krxai_role']=='judge_memory_support_only'
print('OK_V33_6_1_ROUTING_GUARD')
