@echo off
if "%~1"=="" (echo Usage: KRXA_REGISTER_HTTPS_NODE.bat https://YOUR_URL& pause& exit /b 2)
python scripts\register_https_node.py %1
pause
