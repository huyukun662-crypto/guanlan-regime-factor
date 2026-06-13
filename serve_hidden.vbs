' 隐藏窗口启动 serve.bat（供计划任务调用，不弹黑窗）
Dim shell, scriptDir
Set shell = CreateObject("Wscript.Shell")
scriptDir = Left(WScript.ScriptFullName, InStrRev(WScript.ScriptFullName, "\"))
shell.Run """" & scriptDir & "serve.bat""", 0, False
