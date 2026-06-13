# Register / remove the nightly FOF refresh as a Windows Scheduled Task (local, 20:00 daily).
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\setup_schedule.ps1            # install (20:00)
#   powershell -ExecutionPolicy Bypass -File scripts\setup_schedule.ps1 -Time 21:30
#   powershell -ExecutionPolicy Bypass -File scripts\setup_schedule.ps1 -Remove

param(
  [string]$Time = "20:00",
  [switch]$Remove
)

$TaskName = "FOF_DailyRefresh"
$Bat = (Resolve-Path "$PSScriptRoot\daily_refresh.bat").Path

if ($Remove) {
  schtasks /Delete /TN $TaskName /F
  Write-Host "Removed scheduled task $TaskName"
  return
}

# /F overwrites if it already exists. Runs as the current user, when logged on.
schtasks /Create /TN $TaskName /TR "`"$Bat`"" /SC DAILY /ST $Time /F
Write-Host "Installed $TaskName -> runs $Bat daily at $Time"
schtasks /Query /TN $TaskName /FO LIST | Select-String "TaskName|Next Run Time|Schedule|Status"
