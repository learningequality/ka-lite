@echo off

echo.
echo """"""""""""""""""""""""""""""""""""""
echo "   _   __  ___    _     _ _         "
echo "  | | / / / _ \  | |   (_) |        "
echo "  | |/ / / /_\ \ | |    _| |_ ___   "
echo "  |    \ |  _  | | |   | | __/ _ \  "
echo "  | |\  \| | | | | |___| | ||  __/  "
echo "  \_| \_/\_| |_/ \_____/_|\__\___|  "
echo "                                    "
echo " http://kalite.learningequality.org "
echo "                                    "
echo """"""""""""""""""""""""""""""""""""""
echo.

setlocal enabledelayedexpansion

copy %0 kalite\writetest.temp > nul

if %ERRORLEVEL% == 1 (
	echo -------------------------------------------------------------------
	echo You do not have permission to write to this directory!
	echo -------------------------------------------------------------------
	exit /B
) else (
	if %ERRORLEVEL% == 0 (
		del kalite\writetest.temp > nul
	)
)

cd kalite

if exist database\data.sqlite (
    echo -------------------------------------------------------------------
    echo Error: Database file already exists! If this is a new installation,
    echo you should delete the file kalite/database/data.sqlite and then
    echo re-run this script.
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)

reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths" | findstr /I "python.exe" > nul
if !ERRORLEVEL! EQU 1 (
    echo -------------------------------------------------------------------
    echo Error: You do not seem to have Python installed.
    echo Please install version 2.6 or 2.7, and re-run this script.
    echo -------------------------------------------------------------------
    cd ..
    exit /b
)

start /b /wait python.exe -c "import sys; sys.version_info[0]==2 and sys.version_info[1] >= 6 and sys.exit(0) or sys.exit(1)"
if ERRORLEVEL 1 (
    echo -------------------------------------------------------------------
    echo Error: You must have Python version 2.6 or 2.7 installed.
    echo Your version is:
    start /b /wait python.exe -V
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)

echo -------------------------------------------------------------------
echo.
echo This script will configure the database and prepare it for use.
echo.
echo -------------------------------------------------------------------
echo.
pause

start /b /wait python.exe manage.py syncdb --migrate --noinput

echo.
start /b /wait python.exe manage.py generatekeys
echo.

echo.
echo Please choose a username and password for the admin account on this device.
echo You must remember this login information, as you will need to enter it to
echo administer this installation of KA Lite.
echo.
start /b /wait python.exe manage.py createsuperuser --email=dummy@learningequality.org
echo.

set /p name=Please enter a name for this server (or, press Enter to use the default): 
set /p description=Please enter a description for this server (or, press Enter to leave blank): 
start /b /wait python.exe manage.py initdevice "%name%" "%description%"

:choice
echo.
echo Do you wish to set the KA Lite server to run in the background automatically
set /P c=when you start Windows [Y/N]?
if /I "%c%" EQU "Y" goto :yes
if /I "%c%" EQU "N" goto :no
goto :choice
:yes
createshortcut.vbs
echo A link to start.bat was added to the Start Menu's Startup (all users) folder.
echo.
:no

echo -------------------------------------------------------------------
echo.
echo CONGRATULATIONS! You've finished installing the KA Lite software.
echo Please run 'start.bat' to start the server, and then load the url
echo http://127.0.0.1:8008/ to complete the device configuration.
echo.
echo -------------------------------------------------------------------

cd ..

pause
