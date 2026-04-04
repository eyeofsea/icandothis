' SCM Risk Intelligence Platform — Silent Launcher
' Runs launch-app.ps1 without showing a terminal window.

Set shell = CreateObject("WScript.Shell")
scriptDir = Replace(WScript.ScriptFullName, WScript.ScriptName, "")
psScript = scriptDir & "launch-app.ps1"
shell.Run "powershell.exe -ExecutionPolicy Bypass -WindowStyle Hidden -File """ & psScript & """", 0, False
