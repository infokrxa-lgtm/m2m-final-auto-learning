
import os, importlib.util, json
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v32_9_3_STABLE_UI_RUNTIME_FIX/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# direct render tests
for role in ['user','admin','dev']:
    html=m.krxa_v326_real_control_center_html(role)
    assert 'KRXA' in html, role
    assert 'LLM CONTROL' in html, role
    assert 'llmControlStatus' in html, role
    print('ROLE_OK', role, len(html))

st=m.krxa_v329_llm_control_status()
assert st['ok'] is True
assert st['schema']=='KRXA_LLM_CONTROL_BAR_STATUS_V32_9'
print('STATUS_OK', st['llm_mode'], st['api_key_state'])
