
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_3_1_NATURAL_FLOW_AUTO_FREE_START/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert hasattr(m, 'krxa_v33631_chatgpt_proxy_run_auto_free')
assert '무료 5분 세션을 자동 시작' in m.krxa_v33631_chatgpt_proxy_run_auto_free.__doc__
print('OK_V33_6_3_1_AUTO_FREE')
