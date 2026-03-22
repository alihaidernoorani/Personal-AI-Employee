@echo off
REM AI Employee: Process Needs_Action task
REM Called by Windows Task Scheduler daily at 09:00

set PROJECT=C:\Users\DELL\Documents\GitHub\Personal_AI_Employee
set CLAUDE=C:\Users\DELL\AppData\Roaming\npm\claude.cmd
set LOG=%TEMP%\ai-employee-tasks.log

echo [%DATE% %TIME%] === Process Needs_Action START === >> "%LOG%" 2>&1
cd /d "%PROJECT%"
"%CLAUDE%" --print "Run the process-needs-action skill" --permission-mode bypassPermissions >> "%LOG%" 2>&1
echo [%DATE% %TIME%] === Process Needs_Action END (exit %ERRORLEVEL%) === >> "%LOG%" 2>&1
