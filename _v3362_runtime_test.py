
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_2_DB_PASS_LLM_PIPELINE_FULL/app.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
assert m.krxa_v3362_router_classify('안녕하세요')['llm_required'] == False
assert m.krxa_v3362_router_classify('문장 구조에 대해 설명해줘')['llm_required'] == True
assert m.krxa_v3362_router_classify('삼성전자 전략 보고서 작성')['llm_required'] == True
assert m.krxa_v3362_router_status()['policy']['db_direct_output'] == 'blocked'
print('OK_V33_6_2')
