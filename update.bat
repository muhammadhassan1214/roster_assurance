@echo off
pause
echo ================================================
echo Update complete!
echo ================================================
echo.
git stash
git pull
cd /d "%~dp0"
echo ================================================
echo Updating Resend eCards Automation from Git...
echo ================================================

