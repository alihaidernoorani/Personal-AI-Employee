@echo off
REM AI Employee - All Watchers
REM Runs all watchers with automatic restart on crash

cd /d %~dp0
echo.
echo ========================================
echo AI Employee - Process Supervisor
echo ========================================
echo.
echo This will run all watchers with auto-restart:
echo - FilesystemWatcher (file drops)
echo - ApprovalWatcher (approval workflow)
echo - WhatsAppWatcher (keyword detection)
echo.
echo Setting environment variables...
set VAULT_PATH=.\AI_Employee_Vault

echo.
echo Starting all watchers...
echo Logs: %VAULT_PATH%\Logs\
echo.
echo Press Ctrl+C to stop
echo ----------------------------------------
echo.

python process_supervisor.py --watcher all

echo.
echo ========================================
echo Process supervisor stopped
echo ========================================
pause
