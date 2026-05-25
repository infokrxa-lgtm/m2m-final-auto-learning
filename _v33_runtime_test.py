
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_0_DEV_SOURCE_TREE_USER_RESULT_RENDER/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
assert m.krxa_v330_dev_source_tree()['ok']
r=m.krxa_v330_dev_source_read('app.py')
assert r['ok'] and 'KRXAHandler' in r['content']
h=m.krxa_v330_dev_source_editor_html('app.py')
assert '프로그램 트리' in h and '완료/저장' in h
u=m.krxa_v326_real_control_center_html('user')
assert 'resultCards' in u and 'renderUserResult' in u
print('OK_V33_DEV_TREE_RESULT_RENDER')
