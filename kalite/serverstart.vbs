Set oShell = WScript.CreateObject("WScript.Shell")
Set oProc = oShell.Run("python manage.py runwsgiserver host=0.0.0.0 port=8008 threads=50", 0, True)