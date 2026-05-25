
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_6_3_CHATGPT_PROXY_NATURAL_CONVERSATION_FULL/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert 'KRXA 초청문' in m.krxa_v3363_invitation_prompt()
assert m.krxa_v3363_requires_chatgpt('바로 통역을 해야지')[0]
assert m.krxa_v3363_usage_status('testuser')['policy']['free_trial_minutes']==5
assert m.krxa_v3363_start_session('testuser2', 5, 'free_trial')['remaining_seconds']>0
print('OK_V33_6_3_CHATGPT_PROXY')
