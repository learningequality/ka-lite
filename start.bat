@echo off
cd kalite

REM transfer any previously downloaded content from the old location to the new
move static\videos\* ..\content > nul 2> nul

echo Starting the cron server in the background.
start /B runhidden.vbs "cronstart.bat"
echo Running the web server in the background, on port 8008.
start /B runhidden.vbs "serverstart.bat"
cd ..