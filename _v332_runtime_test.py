
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_2_M2M_PRODUCT_UI_FIELD_BUILD/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
h=m.krxa_v332_m2m_product_html()
assert '말대말 × KRXA' in h
assert 'voiceStart' in h
assert '/api/llm/execute' in h
assert m.krxa_v332_is_llm_execute_command('LLM 실행: 삼성전자 전략 분석')
assert m.krxa_v332_strip_llm_command('LLM 실행: 삼성전자 전략 분석') == '삼성전자 전략 분석'
st=m.krxa_v332_m2m_status()
assert st['ok'] and '/m2m-product' in st['routes']
print('OK_V33_2_M2M_PRODUCT_FIELD')
