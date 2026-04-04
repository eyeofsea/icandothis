# Creates a desktop shortcut for SCM Risk Intelligence Platform

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$VbsPath = Join-Path $ProjectRoot "scripts\launch-app.vbs"
$IconPath = Join-Path $ProjectRoot "frontend\src\app\favicon.ico"
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$ShortcutPath = Join-Path $DesktopPath "SCM Risk Intelligence.lnk"

$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($ShortcutPath)
$Shortcut.TargetPath = $VbsPath
$Shortcut.WorkingDirectory = $ProjectRoot
$Shortcut.Description = "SCM Risk Intelligence Platform"
$Shortcut.WindowStyle = 7  # Minimized

if (Test-Path $IconPath) {
    $Shortcut.IconLocation = "$IconPath,0"
}

$Shortcut.Save()

Write-Host "Desktop shortcut created: $ShortcutPath" -ForegroundColor Green
