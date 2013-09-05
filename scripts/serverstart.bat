@echo off

rem have to change directory, in order to make sure we can import settings
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%\..\kalite"

call "%SCRIPT_DIR%\get_port.bat" %*
for /f %%a in ('start /b python.exe -c "import settings; print settings.CHERRYPY_THREAD_COUNT"') do set NTHREADS=%%a

echo.
start /b python.exe "%SCRIPT_DIR%\manage.py" runcherrypyserver host=0.0.0.0 port=%PORT% daemonize=True threads=%NTHREADS% pidfile="%SCRIPT_DIR%\runcherrypyserver.pid"

cd "%OLD_DIR%"