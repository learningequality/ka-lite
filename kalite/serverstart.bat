@echo off
cd `dirname "${BASH_SOURCE[0]}"`
echo.
echo Running the web server in the background, on port 8008.
python manage.py runwsgiserver host=0.0.0.0 port=8008 threads=50
echo The server should now be accessible locally at: http://127.0.0.1:8008/
echo To access it from another connected computer, try the following address(es):
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"IP Address"') do (
    for /f "tokens=1 delims= " %%a in ("%%i") do echo http://%%a:8008/
)