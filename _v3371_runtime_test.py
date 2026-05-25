
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_7_1_BILLING_UX_CONTROL_FULL/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cfg=m.krxa_v3371_load_billing_config()
assert cfg['billing_mode'] in ['ON','OFF']
assert cfg['free_minutes']==10
assert cfg['paid_options']==[10,20,30]
html=m.krxa_v3371_control_html()
assert 'AI 과금 모드' in html and '무료 10분' in html
st=m.krxa_v3371_status('tester')
assert st['ok'] and st['config']['free_minutes']==10
print('OK_V33_7_1_BILLING_UX')
