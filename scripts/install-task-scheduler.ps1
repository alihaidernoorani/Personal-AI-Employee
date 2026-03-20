# install-task-scheduler.ps1 — Install Silver Tier scheduled tasks on Windows
#
# Creates three Windows Task Scheduler entries:
#   1. Gmail poll       — every 5 minutes (all day)
#   2. LinkedIn post    — Monday at 08:00
#   3. Process tasks    — daily at 09:00
#
# Usage (run as Administrator):
#   powershell -ExecutionPolicy Bypass -File scripts\install-task-scheduler.ps1
#
# To remove all tasks later:
#   Unregister-ScheduledTask -TaskName "AIEmployee-*" -Confirm:$false

$ErrorActionPreference = "Stop"

# ---------------------------------------------------------------------------
# Resolve project root and Python path
# ---------------------------------------------------------------------------
$ScriptDir  = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$EnvFile    = Join-Path $ProjectDir ".env"

# Load VAULT_PATH from .env (simple key=value parser)
$VaultPath = $null
if (Test-Path $EnvFile) {
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match '^\s*VAULT_PATH\s*=\s*(.+)$') {
            # Convert WSL2 /mnt/c/... path to Windows C:\... path if needed
            $raw = $Matches[1].Trim()
            if ($raw -match '^/mnt/([a-z])/(.*)') {
                $VaultPath = "$($Matches[1].ToUpper()):\$($Matches[2] -replace '/', '\')"
            } else {
                $VaultPath = $raw
            }
        }
    }
}
if (-not $VaultPath) {
    $VaultPath = Join-Path $ProjectDir "AI_Employee_Vault"
}

# Prefer venv Python; fall back to system Python313
$PythonVenv = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$Python313  = "C:\Program Files\Python313\python.exe"
$Python     = if (Test-Path $PythonVenv) { $PythonVenv } elseif (Test-Path $Python313) { $Python313 } else { "python" }

$Orchestrator = Join-Path $ProjectDir "orchestrator.py"
$LogFile      = Join-Path $env:TEMP "ai-employee-tasks.log"

# Claude Code CLI path
$Claude = "C:\Users\DELL\AppData\Roaming\npm\claude.cmd"

Write-Host ""
Write-Host "=== AI Employee — Windows Task Scheduler Setup ===" -ForegroundColor Cyan
Write-Host "Project   : $ProjectDir"
Write-Host "Vault     : $VaultPath"
Write-Host "Python    : $Python"
Write-Host "Log file  : $LogFile"
Write-Host ""

# ---------------------------------------------------------------------------
# Helper: register or update a task
# ---------------------------------------------------------------------------
function Register-AITask {
    param(
        [string]$TaskName,
        [string]$Description,
        [string]$Executable,
        [string]$Arguments,
        [object]$Trigger,
        [string]$WorkingDir
    )

    $existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "  [update] $TaskName" -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    } else {
        Write-Host "  [add]    $TaskName" -ForegroundColor Green
    }

    $action = New-ScheduledTaskAction `
        -Execute $Executable `
        -Argument $Arguments `
        -WorkingDirectory $WorkingDir

    $settings = New-ScheduledTaskSettingsSet `
        -ExecutionTimeLimit (New-TimeSpan -Minutes 10) `
        -StartWhenAvailable `
        -DontStopIfGoingOnBatteries `
        -RunOnlyIfNetworkAvailable

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Description $Description `
        -Action $action `
        -Trigger $Trigger `
        -Settings $settings `
        -Principal $principal `
        -Force | Out-Null
}

# ---------------------------------------------------------------------------
# Task 1: Gmail poll — every 5 minutes
# ---------------------------------------------------------------------------
$gmailArgs = "`"$Orchestrator`" --watcher gmail --cron >> `"$LogFile`" 2>&1"
$gmailTrigger = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Minutes 5) -Once -At (Get-Date)

Register-AITask `
    -TaskName    "AIEmployee-GmailPoll" `
    -Description "AI Employee: Poll Gmail every 5 minutes for new emails" `
    -Executable  $Python `
    -Arguments   $gmailArgs `
    -Trigger     $gmailTrigger `
    -WorkingDir  $ProjectDir

# ---------------------------------------------------------------------------
# Task 2: LinkedIn post — Monday at 08:00
# ---------------------------------------------------------------------------
$linkedinArgs = "--print `"Run the linkedin-post skill`" >> `"$LogFile`" 2>&1"
$linkedinTrigger = New-ScheduledTaskTrigger -Weekly -WeeksInterval 1 -DaysOfWeek Monday -At "08:00"

Register-AITask `
    -TaskName    "AIEmployee-LinkedInPost" `
    -Description "AI Employee: Generate weekly LinkedIn lead-gen post draft (Monday 08:00)" `
    -Executable  $Claude `
    -Arguments   $linkedinArgs `
    -Trigger     $linkedinTrigger `
    -WorkingDir  $ProjectDir

# ---------------------------------------------------------------------------
# Task 3: Process Needs_Action — daily at 09:00
# ---------------------------------------------------------------------------
$processArgs = "--print `"Run the process-needs-action skill`" >> `"$LogFile`" 2>&1"
$processTrigger = New-ScheduledTaskTrigger -Daily -At "09:00"

Register-AITask `
    -TaskName    "AIEmployee-ProcessTasks" `
    -Description "AI Employee: Process all pending Needs_Action items (daily 09:00)" `
    -Executable  $Claude `
    -Arguments   $processArgs `
    -Trigger     $processTrigger `
    -WorkingDir  $ProjectDir

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
Write-Host ""
Write-Host "=== Installed tasks ===" -ForegroundColor Cyan
Get-ScheduledTask -TaskName "AIEmployee-*" | Format-Table TaskName, State -AutoSize

Write-Host "Log file: $LogFile"
Write-Host ""
Write-Host "To run a task immediately for testing:" -ForegroundColor Yellow
Write-Host "  Start-ScheduledTask -TaskName 'AIEmployee-GmailPoll'"
Write-Host "  Start-ScheduledTask -TaskName 'AIEmployee-LinkedInPost'"
Write-Host "  Start-ScheduledTask -TaskName 'AIEmployee-ProcessTasks'"
Write-Host ""
Write-Host "To remove all tasks:"
Write-Host "  Unregister-ScheduledTask -TaskName 'AIEmployee-*' -Confirm:`$false"
