@echo off
setlocal

echo ================================================
echo Roster Assurance Automation...
echo ================================================
cd /d "%~dp0"

rem Activate venv if available so correct dependencies are used
if exist "%~dp0venv\Scripts\activate.bat" (
    call "%~dp0venv\Scripts\activate.bat"
) else (
    echo [WARN] No venv found at %~dp0venv; using system Python.
)

python -m streamlit run script/main.py

pause
