@echo off

copy %0 kalite

if %ERRORLEVEL% == 1 (
	echo -------------------------------------------------------------------
	echo You have no permissions to write on this directory!
	echo You must change your permissions or copy/clone all files to 
	echo a directory where you have permissions to write and then 
	echo re-run this script.
	echo -------------------------------------------------------------------
	exit /B
) else (
	if %ERRORLEVEL% == 0 (
		del kalite\%0
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

python -c "import sys; sys.version_info[0]==2 and sys.version_info[1] >= 5 and sys.exit(0) or sys.exit(1)"
if ERRORLEVEL 1 (
    echo -------------------------------------------------------------------
    echo Error: You must have Python version 2.6 or 2.7 installed.
    echo Your version is:
    python -V
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)
if ERRORLEVEL 9009 (
    echo -------------------------------------------------------------------
    echo Error: You do not seem to have Python installed, or it is not on
    echo the PATH. Install version 2.6 or 2.7, and re-run this script.
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)

echo -------------------------------------------------------------------
echo.
echo This script will configure the database and prepare it for use.
echo.
echo When asked if you want to create a superuser, type 'yes' and enter
echo your details. You must remember this login information, as you will
echo need to enter it to administer the website.
echo.
echo -------------------------------------------------------------------
echo.
pause

python manage.py syncdb --migrate

echo.
python manage.py generatekeys
echo.

set /p name=Please enter a name for this server (or, press Enter to use the default): 
set /p description=Please enter a description for this server (or, press Enter to leave blank): 
python manage.py initdevice "%name%" "%description%"

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
