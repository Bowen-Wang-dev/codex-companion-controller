@echo off
chcp 65001 >nul
setlocal
set "COMPANION_LANGUAGE=zh-CN"
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if defined CONTROLLER_MODERN_PYTHON (
  "%CONTROLLER_MODERN_PYTHON%" "%~dp0scripts\setup_windows.py" %*
) else (
  python "%~dp0scripts\setup_windows.py" %*
)
set "COMPANION_EXIT=%ERRORLEVEL%"
if not "%COMPANION_EXIT%"=="0" set /p "COMPANION_CLOSE=按回车关闭窗口。"
exit /b %COMPANION_EXIT%
