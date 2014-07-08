@echo off
set "SCRIPT_DIR=%~dp0"
set "KALITE_DIR=%SCRIPT_DIR%\kalite"
setlocal enabledelayedexpansion

copy %0 "%KALITE_DIR%\writetest.temp" > nul
if %ERRORLEVEL% == 1 (
    echo -------------------------------------------------------------------
    echo You do not have permission to write to this directory!
    echo -------------------------------------------------------------------
    exit /B
) else (
    if exist "%KALITE_DIR%\writetest.temp" (
        del "%KALITE_DIR%\writetest.temp" > nul
    )
)

rem Check for Python
rem
call "%SCRIPT_DIR%\scripts\python.bat"
if !ERRORLEVEL! EQU 1 (
    echo -------------------------------------------------------------------
    echo Error: You do not seem to have Python installed.
    echo Please install version 2.6 or 2.7, and re-run this script.
    echo -------------------------------------------------------------------
    cd ..
    exit /b
)

rem Setup script
rem
start /b /wait python.exe "%KALITE_DIR%\manage.py" setup

rem Run at startup
rem
:choice
echo.
echo Do you wish to set the KA Lite server to run in the background automatically
set /P c=when you start Windows [Y/N]?
if /I "%c%" EQU "Y" goto :yes
if /I "%c%" EQU "N" goto :no
goto :choice
:yes
"%SCRIPT_DIR%\scripts\createshortcut.vbs"
echo A link to start.bat was added to the Start Menu's Startup (all users) folder.
echo.
:no

pause
