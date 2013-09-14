@echo off
set SCRIPT_DIR=%~dp0
setlocal enabledelayedexpansion

copy %0 "%SCRIPT_DIR%\kalite\writetest.temp > nul

if %ERRORLEVEL% == 1 (
	echo -------------------------------------------------------------------
	echo You do not have permission to write to this directory!
	echo -------------------------------------------------------------------
	exit /B
) else (
	if %ERRORLEVEL% == 0 (
		del "%SCRIPT_DIR%\kalite\writetest.temp > nul
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

rem Installer script
rem
start /b /wait python.exe "%SCRIPT_DIR%\kalite\manage.py" install

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
