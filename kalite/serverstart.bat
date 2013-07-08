rem @echo off
if "%1" == "" (
    set PORT=8008
) else (
    set PORT=%1
)
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%"
echo.
start /b python.exe manage.py runcherrypyserver host=0.0.0.0 port=8008 daemonize=True threads=50 pidfile="%SCRIPT_DIR%\runcherrypyserver.pid"
CD "%OLD_DIR%"