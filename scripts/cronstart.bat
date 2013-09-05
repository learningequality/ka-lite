@echo off
echo.
rem TODO(ruimalheiro): Create a more general python script to be crossplatform.
start /b python.exe -c "import subprocess; sp=subprocess.Popen(['python', 'cronserver.py']);f=open('cronserver.pid','w'); f.write(str(sp.pid)); f.close(); exit();"