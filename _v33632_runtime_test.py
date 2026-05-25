
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_3_2_FLOW_GATE_SUPPORT_FIX/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
a=m.krxa_v33632_free_local_answer('u','마이크를 바꿔야 하나?')
assert a and a['free_support'] and '마이크' in a['final']
b=m.krxa_v33632_free_local_answer('u','지금 몇 시야?')
assert b and '한국 기준 현재 시간' in b['final']
print('OK_V33_6_3_2_FLOW_GATE_SUPPORT')
