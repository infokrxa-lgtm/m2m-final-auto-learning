# KRXA V33.1 RENDER + GIT AUTO DEPLOY

## 핵심
- Render는 유지합니다.
- 개발자 UI에서 수정 후 GitHub 자동 반영 버튼을 추가했습니다.
- GitHub 반영 후 Render Auto Deploy가 자동 재배포합니다.

## 추가 API
- GET /api/dev/deploy/config
- POST /api/dev/deploy/github

## 필요한 환경변수
- GITHUB_TOKEN
- GITHUB_REPO=infokrxa-lgtm/KRXA
- GITHUB_BRANCH=main

## 체크
- [OK] py_compile_app_py — OK
- [OK] runtime_deploy_config_and_editor — OK_V33_1_DEPLOY_AUTOMATION
Spreadsheet runtime warmup failed during python startup
Traceback (most recent call last):
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/patches/warm_spreadsheet_runtime_on_startup.py", line 26, in warm_spreadsheet_runtime_on_startup
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/spreadsheet_warmup.py", line 785, in warm_spreadsheet_runtime
  File "/tmp/tmp.9eeVjt35CN/artifact_tool_v2-2.7.5/artifact_tool/spreadsheet_warmup.py", line

## 패치
- add_v331_github_auto_deploy_helpers: 
- add_deploy_config_get_route: 
- add_deploy_github_post_route: 
- add_deploy_buttons_and_js_to_dev_editor: 