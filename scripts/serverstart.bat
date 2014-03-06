@echo off

rem have to change directory, in order to make sure we can import settings
set "SCRIPT_DIR=%~dp0"
set "KALITE_DIR=%SCRIPT_DIR%\..\kalite"

CALL "%SCRIPT_DIR%\get_port.bat" %*
CALL "%SCRIPT_DIR%\get_setting.bat" CHERRYPY_THREAD_COUNT NTHREADS

IF EXIST "%KALITE_DIR%\runcherrypyserver.pid" (
    CALL "%SCRIPT_DIR%\serverstop.bat"
)

echo.
start /b python.exe "%KALITE_DIR%\manage.py" kaserve host=0.0.0.0 port=%PORT% daemonize=True threads=%NTHREADS% pidfile="%KALITE_DIR%\runcherrypyserver.pid"

