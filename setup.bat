@echo off
setlocal

:: Setup environment for Roster Assurance Automation
cd /d "%~dp0"

set VENV_DIR=%~dp0venv
set ACTIVATE=%VENV_DIR%\Scripts\activate.bat

if not exist "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

if exist "%ACTIVATE%" (
    call "%ACTIVATE%"
) else (
    echo [ERROR] Failed to find activate script at %ACTIVATE%
    pause
    exit /b 1
)

echo [INFO] Installing dependencies...
pip install --upgrade pip
if exist "%~dp0requirements.txt" (
    pip install -r "%~dp0requirements.txt"
) else (
    echo [WARN] requirements.txt not found; skipping dependency install.
)

echo [INFO] Setup complete. Activate with:
if exist "%ACTIVATE%" (
    echo    call "%ACTIVATE%"
)

endlocal

