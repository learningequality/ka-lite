@echo off

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
    echo Error: You must have Python version 2.5, 2.6, or 2.7 installed.
    echo Your version is:
    python -V
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)
if ERRORLEVEL 9009 (
    echo -------------------------------------------------------------------
    echo Error: You do not seem to have Python installed, or it is not on
    echo the PATH. Install version 2.5, 2.6, or 2.7, and re-run this script.
    echo -------------------------------------------------------------------
    cd ..
    exit /B
)

cd ..

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

cd kalite

python manage.py syncdb --migrate

cd ..
