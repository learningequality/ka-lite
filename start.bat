@echo off
cd kalite
if exist database\data.sqlite (
echo Starting the cron server in the background.
start /B runhidden.vbs "cronstart.bat"
echo Running the web server in the background, on port 8008.
start /B runhidden.vbs "serverstart.bat"
cd ..
) else (
echo Run install.bat first!
)