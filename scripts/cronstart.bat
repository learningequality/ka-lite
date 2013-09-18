@echo off
rem have to change directory, in order to make sure we can import settings
set SCRIPT_DIR=%~dp0
set KALITE_DIR=%SCRIPT_DIR%\..\kalite

CALL "%SCRIPT_DIR%\get_setting.bat" CRONSERVER_FREQUENCY FREQ

echo.
start /b python.exe -c "import sys, subprocess; sp=subprocess.Popen([sys.executable, '%KALITE_DIR%\manage.py', 'cronserver', '%FREQ%']);f=open('%KALITE_DIR%\cronserver.pid','w'); f.write(str(sp.pid)); f.close(); exit();"
