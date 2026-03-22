@echo off
REM AI Employee: LinkedIn Post task
REM Called by Windows Task Scheduler every Monday at 08:00

set PROJECT=C:\Users\DELL\Documents\GitHub\Personal_AI_Employee
set CLAUDE=C:\Users\DELL\AppData\Roaming\npm\claude.cmd
set LOG=%TEMP%\ai-employee-tasks.log

echo [%DATE% %TIME%] === LinkedIn Post START === >> "%LOG%" 2>&1
cd /d "%PROJECT%"
"%CLAUDE%" --print "Run the linkedin-post skill" --permission-mode bypassPermissions >> "%LOG%" 2>&1
echo [%DATE% %TIME%] === LinkedIn Post END (exit %ERRORLEVEL%) === >> "%LOG%" 2>&1
