Set oShell = CreateObject("WScript.Shell")

Set sPath = oShell.SpecialFolders("AllUsersStartup")
Set oShortcut = oShell.CreateShortcut(sPath & "\ka-lite.lnk")
oShortcut.TargetPath = oShell.CurrentDirectory & "\..\start.bat"
oShortcut.Save