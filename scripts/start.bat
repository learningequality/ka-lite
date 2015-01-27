@echo off

echo RUNNING THIS SCRIPT IS DEPRECATED
echo Use bin\windows\kalite.bat

rem determine the script directory (could be in scripts, could be in root folder)
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%\python.bat" (
    set "KALITE_DIR=%SCRIPT_DIR%\..\kalite"
) else (
    set "SCRIPT_DIR=%SCRIPT_DIR%\scripts"
    set "KALITE_DIR=%SCRIPT_DIR%\kalite"
)

set "file_exist="
if exist "%KALITE_DIR%\cronserver.pid" set file_exist=0
if exist "%KALITE_DIR%\runcherrypyserver.pid" set file_exist=0
if defined file_exist (
    call "%SCRIPT_DIR%\stop.bat"
)

call "%SCRIPT_DIR%\python.bat"
if !ERRORLEVEL! EQU 1 (
    echo -------------------------------------------------------------------
    echo Error: You do not seem to have Python installed.
    echo Please install version 2.6 or 2.7, and re-run this script.
    echo -------------------------------------------------------------------
    exit /b
)

echo Starting the cron server in the background.
call "%SCRIPT_DIR%\cronstart.bat" %1

echo Running the web server in the background.
call "%SCRIPT_DIR%\serverstart.bat"
