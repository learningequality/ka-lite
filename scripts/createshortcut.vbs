Set oShell = CreateObject("WScript.Shell")

sPath = oShell.SpecialFolders("Startup")
Set oShortcut = oShell.CreateShortcut(sPath & "\ka-lite.lnk")
oShortcut.TargetPath = oShell.CurrentDirectory & "\..\start.bat"
oShortcut.WorkingDirectory = oShell.CurrentDirectory & "\..\"
oShortcut.Save
