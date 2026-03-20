$ProjectDir = 'C:\Users\DELL\Documents\GitHub\Personal_AI_Employee'
$Python     = 'C:\Program Files\Python313\python.exe'
$Claude     = 'C:\Users\DELL\AppData\Roaming\npm\claude.cmd'
$BashExe    = 'C:\Program Files\Git\bin\bash.exe'
$LogFile    = "$env:TEMP\ai-employee-tasks.log"
$Orch       = "$ProjectDir\orchestrator.py"
$Scheduler  = "$ProjectDir\scheduler.sh"

function Install-AITask($name, $desc, $exe, $taskArgs, $trigger) {
    $action   = New-ScheduledTaskAction -Execute $exe -Argument $taskArgs -WorkingDirectory $ProjectDir
    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 4) `
        -StartWhenAvailable `
        -DontStopIfGoingOnBatteries
    $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    if ($existing) { Unregister-ScheduledTask -TaskName $name -Confirm:$false }
    Register-ScheduledTask -TaskName $name -Description $desc `
        -Action $action -Trigger $trigger -Settings $settings -Force | Out-Null
    Write-Host "  [OK] $name"
}

Write-Host "`n=== AI Employee - Windows Task Scheduler Setup ===" -ForegroundColor Cyan
Write-Host "Project : $ProjectDir"
Write-Host "Python  : $Python"
Write-Host "Claude  : $Claude"
Write-Host "Log     : $LogFile`n"

# Task 1: Gmail poll every 5 minutes
$t1 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Install-AITask `
    'AIEmployee-GmailPoll' `
    'AI Employee: Poll Gmail every 5 minutes' `
    $Python `
    "`"$Orch`" --watcher gmail --cron >> `"$LogFile`" 2>&1" `
    $t1

# Task 2: Process Needs_Action every 5 minutes via scheduler.sh
$t2 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)
Install-AITask `
    'AIEmployee-ProcessNeedsAction' `
    'AI Employee: Process Needs_Action every 5 minutes via scheduler.sh' `
    $BashExe `
    "`"$Scheduler`" >> `"$LogFile`" 2>&1" `
    $t2

# Task 3: LinkedIn post - Monday 08:00
$t3 = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Monday -At '08:00'
Install-AITask `
    'AIEmployee-LinkedInPost' `
    'AI Employee: Weekly LinkedIn post draft (Monday 08:00)' `
    $Claude `
    "--print `"Run the linkedin-post skill`" --permission-mode bypassPermissions >> `"$LogFile`" 2>&1" `
    $t3

# Task 4: Daily process at 09:00
$t4 = New-ScheduledTaskTrigger -Daily -At '09:00'
Install-AITask `
    'AIEmployee-DailyProcess' `
    'AI Employee: Daily Needs_Action processing at 09:00' `
    $Claude `
    "--print `"Run the process-needs-action skill`" --permission-mode bypassPermissions >> `"$LogFile`" 2>&1" `
    $t4

Write-Host "`n=== Installed Tasks ===" -ForegroundColor Green
Get-ScheduledTask -TaskName 'AIEmployee-*' | Format-Table TaskName, State -AutoSize
Write-Host "Log file: $LogFile"
Write-Host "`nTest a task now:"
Write-Host "  Start-ScheduledTask -TaskName 'AIEmployee-ProcessNeedsAction'"
