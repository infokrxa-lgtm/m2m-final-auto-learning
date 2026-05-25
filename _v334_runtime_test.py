
import os, importlib.util
os.environ.setdefault('PORT','10000')
spec=importlib.util.spec_from_file_location('app_test', r'/mnt/data/KRXA_LOCAL_BUILD_v33_4_M2M_ONLY_DEVICE_AUDIO_FIELD_BUILD/app.py')
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
u=m.krxa_v334_m2m_user_html()
assert '마이크' in u and '스피커' in u and 'detectDevices' in u and 'SpeechSynthesisUtterance' in u
assert 'uploadFile' in u and 'openUploadEditor' in u
assert '말대말 관제' in m.krxa_v334_m2m_control_html()
assert '말대말 개발자 UI' in m.krxa_v334_m2m_dev_html()
assert '업로드 편집기' in m.krxa_v334_m2m_editor_html()
st=m.krxa_v334_m2m_only_status(); assert st['ok'] and st['device_audio']['microphone_auto_detect']
print('OK_V33_4_M2M_ONLY_DEVICE_AUDIO_FIELD')
