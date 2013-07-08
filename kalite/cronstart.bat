@echo off
echo.
start /b python.exe -c "import subprocess; sp=subprocess.Popen(['python', 'cronserver.py']);f=open('cronserver.pid','w'); f.write(str(sp.pid)); f.close(); exit();"