
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_1_RENDER_GIT_AUTO_DEPLOY/app.py')
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
cfg=m.krxa_v331_deploy_config()
assert cfg['schema']=='KRXA_RENDER_GIT_AUTO_DEPLOY_CONFIG_V33_1'
h=m.krxa_v330_dev_source_editor_html('app.py')
assert 'Git 자동배포' in h and 'deployGit' in h
print('OK_V33_1_DEPLOY_AUTOMATION')
