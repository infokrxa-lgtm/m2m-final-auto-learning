
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_5_M2M_NATURAL_VOICE_REAL_CONTROL_UI_APPLY/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert '자연 대화 시작' in m.krxa_v335_m2m_user_html()
assert '개발자 요청 승인' in m.krxa_v335_m2m_control_html()
assert '관제 승인 요청' in m.krxa_v335_m2m_dev_html()
r=m.krxa_v335_dev_request_create('test','user_ui','ui_apply','content','dev')
assert r['ok']
st=m.krxa_v335_control_status()
assert st['ok']
print('OK_V33_5')
