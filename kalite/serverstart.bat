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
echo Running the web server in the background, on port %PORT%.
python manage.py runcherrypyserver host=0.0.0.0 port=%PORT% daemonize=True threads=50 pidfile="%SCRIPT_DIR%\runcherrypyserver.pid"
echo The server should now be accessible locally at: http://127.0.0.1:%PORT%/
echo To access it from another connected computer, try the following address(es):
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"IP Address"') do (
    for /f "tokens=1 delims= " %%a in ("%%i") do echo http://%%a:%PORT%/
)
CD "%OLD_DIR%"