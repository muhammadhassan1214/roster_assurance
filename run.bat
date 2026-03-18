@echo off
setlocal

cd /d "%~dp0"
set VENV_DIR=%~dp0venv
set ACTIVATE=%VENV_DIR%\Scripts\activate.bat

if not exist "%ACTIVATE%" (
    echo [ERROR] Virtual environment not found. Please run setup.bat first.
    pause
    exit /b 1
)

call "%ACTIVATE%"

echo ================================================
echo Roster Assurance Automation launching...
echo ================================================
python -m streamlit run script/main.py

pause
