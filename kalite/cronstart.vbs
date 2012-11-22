Set oShell = WScript.CreateObject("WScript.Shell")
Set oProc = oShell.Run("python cronserver.py", 0, True)