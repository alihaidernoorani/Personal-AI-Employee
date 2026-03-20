@echo off
REM Gmail API Watcher for Windows
REM Monitors unread IMPORTANT emails

cd /d %~dp0
echo.
echo ========================================
echo Gmail API Watcher - Windows Native
echo ========================================
echo.
echo Setting environment variables...
set VAULT_PATH=.\AI_Employee_Vault

echo.
echo Starting Gmail API watcher (check_interval=120s)...
echo Monitoring: UNSEEN IMPORTANT emails only
echo.
echo On first run, a browser will open for OAuth authorization.
echo.
echo Message files will be created in: %VAULT_PATH%\Needs_Action\GMAIL_*.md
echo.
echo Press Ctrl+C to stop the watcher
echo ----------------------------------------
echo.

python orchestrator.py --watcher gmail_api

echo.
echo ========================================
echo Watcher stopped
echo ========================================
pause
