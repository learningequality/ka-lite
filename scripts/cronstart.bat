@echo off
rem TODO(ruimalheiro): Create a more general python script to be crossplatform.

rem have to change directory, in order to make sure we can import settings
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%\..\kalite"

echo.
start /b python.exe -c "import subprocess; sp=subprocess.Popen(['python', 'cronserver.py']);f=open('cronserver.pid','w'); f.write(str(sp.pid)); f.close(); exit();"

cd "%OLD_DIR%"