
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_USER_UP_ADMIN_STYLE2_BUILD/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
u=m.krxa_v336_user_up_main_html()
assert '말대말 사용자 UP V33.6' in u and 'openFlow' in u and '대화·통역 메인' in u
a=m.krxa_v336_admin_style2_main_html()
assert '관리자 UI 2번 스타일 V33.6' in a and '실제 통제' in a
p=m.krxa_v336_popup_window_html('site-manager')
assert '사이트 관리' in p
print('OK_V33_6_USER_ADMIN')
