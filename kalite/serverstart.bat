rem @echo off
if "%1" == "" (
    for /f "delims=" %%a in ('start /b python.exe -c "import settings; print settings.PRODUCTION_PORT"') do set PORT=%%a
) else (
    set PORT=%1
)
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%"
echo.
start /b python.exe manage.py runcherrypyserver host=0.0.0.0 port=%PORT% daemonize=True threads=50 pidfile="%SCRIPT_DIR%\runcherrypyserver.pid"
CD "%OLD_DIR%"