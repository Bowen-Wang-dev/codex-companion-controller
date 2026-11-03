@echo off
setlocal
set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"
if defined CONTROLLER_MODERN_PYTHON (
  "%CONTROLLER_MODERN_PYTHON%" "%~dp0scripts\setup_windows.py" %*
) else (
  python "%~dp0scripts\setup_windows.py" %*
)
set "COMPANION_EXIT=%ERRORLEVEL%"
if not "%COMPANION_EXIT%"=="0" pause
exit /b %COMPANION_EXIT%
