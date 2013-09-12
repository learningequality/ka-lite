@echo off
rem have to change directory, in order to make sure we can import settings
set SCRIPT_DIR=%~dp0
set KALITE_DIR=%SCRIPT_DIR%\..\kalite

for /f %%a in ('"%SCRIPT_DIR%\get_setting.bat" CRONSERVER_FREQUENCY') do set FREQ=%%a

echo.
start /b python.exe -c "import sys, subprocess; sp=subprocess.Popen([sys.executable, '%KALITE_DIR%\manage.py', 'cronserver', %FREQ%]);f=open('cronserver.pid','w'); f.write(str(sp.pid)); f.close(); exit();"
