@echo off
REM AI Employee: Gmail Poll task
REM Called by Windows Task Scheduler every 5 minutes

set PROJECT=C:\Users\DELL\Documents\GitHub\Personal_AI_Employee
set PYTHON=C:\Program Files\Python313\python.exe
set LOG=%TEMP%\ai-employee-tasks.log

echo [%DATE% %TIME%] === Gmail Poll START === >> "%LOG%" 2>&1
cd /d "%PROJECT%"
"%PYTHON%" "%PROJECT%\orchestrator.py" --watcher gmail --cron >> "%LOG%" 2>&1
echo [%DATE% %TIME%] === Gmail Poll END (exit %ERRORLEVEL%) === >> "%LOG%" 2>&1
