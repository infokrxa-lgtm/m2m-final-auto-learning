
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_7_CHATGPT_FIRST_KRXAI_LEARNING_FULL/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert 'KRXA → ChatGPT 초청문' in m.krxa_v337_invite_prompt()
st=m.krxa_v337_status('testuser')
assert st['policy']['chatgpt_first'] and st['policy']['router_conditions_removed']
print('OK_V33_7_CHATGPT_FIRST')
