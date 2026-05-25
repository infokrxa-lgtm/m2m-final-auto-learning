
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v32_9_2_FULL_AUDIT_STABLE_FIX/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for r in ['user','admin','dev']:
    h=m.krxa_v326_real_control_center_html(r)
    assert 'LLM CONTROL' in h
    assert 'KRXA' in h
print('OK_ROLES')
print(m.krxa_v329_llm_control_status().get('schema'))
