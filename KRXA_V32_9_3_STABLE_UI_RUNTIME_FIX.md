# KRXA V32.9.3 STABLE UI RUNTIME FIX

## 목적
- V32.9.2 이후에도 발생 가능한 /user 502, JS/HTML 런타임 오류를 줄이는 안정판.
- LLM CONTROL BAR 유지.
- app.py 컴파일 + user/admin/dev 렌더링 + LLM status 함수 테스트 통과.

## 패치
- normalize_llmbar_css: top 88px, flex-wrap, escaped braces
- replace_llm_control_js_safe: DOM-safe status/mode functions

## 체크
- [OK] py_compile_app_py — OK
- [OK] runtime_import_render_roles_status — ROLE_OK user 13261
ROLE_OK admin 13414
ROLE_OK dev 13778
STATUS_OK off MISSING
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/spreadsheet_warmup.py", line 720, in _warm_feature_flows
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/spreadsheet_warmup.py", line 704, in _warm_collaboration_flows
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/generated/interface/models
- [OK] symbol:def krxa_v326_real_control_center_html — def krxa_v326_real_control_center_html
- [OK] symbol:def krxa_v329_llm_control_status — def krxa_v329_llm_control_status
- [OK] symbol:def krxa_v329_set_llm_control_mode — def krxa_v329_set_llm_control_mode
- [OK] symbol:clean_path.startswith('/api/llm/control/statu — clean_path.startswith('/api/llm/control/status')
- [OK] symbol:clean_path.startswith('/api/llm/control/mode' — clean_path.startswith('/api/llm/control/mode')
- [OK] symbol:KRXAI ↔ LLM CONTROL — KRXAI ↔ LLM CONTROL
- [OK] symbol:async function llmControlStatus — async function llmControlStatus
- [OK] no_unresolved_display_placeholder — display placeholder scan