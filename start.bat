@echo off
if "%1" == "" (
  set PORT=8008
) else (
  set PORT=%1
)

cd kalite
if exist database\data.sqlite (
  REM transfer any previously downloaded content from the old location to the new
	move static\videos\* ..\content > nul 2> nul

	echo Starting the cron server in the background.
	start /B runhidden.vbs "cronstart.bat"
	echo Running the web server in the background, on port %PORT%.
	start /B runhidden.vbs "serverstart.bat %PORT%"
) else (
	echo Please run install.bat first!
)
cd ..