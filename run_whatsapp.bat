@echo off
REM WhatsApp Watcher — persistent session, single browser, polls every 30s
cd /d %~dp0

echo.
echo ========================================
echo  WhatsApp Watcher
echo ========================================
echo.
echo  - Browser opens ONCE (session saved)
echo  - QR scan required on FIRST run only
echo  - Polls every 30 seconds
echo  - Task files: AI_Employee_Vault\Needs_Action\WA_*.md
echo.
echo Press Ctrl+C to stop
echo ----------------------------------------
echo.

python launch_watcher.py

echo.
echo ========================================
echo  Watcher stopped
echo ========================================
pause
