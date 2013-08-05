@echo off
cd kalite

if "%1" == "" (
  for /f "delims=" %%a in ('start /b python.exe -c "import settings; print settings.PRODUCTION_PORT"') do set PORT=%%a
) else (
  set PORT=%1
)

if exist database\data.sqlite (
  REM transfer any previously downloaded content from the old location to the new
	move static\videos\* ..\content > nul 2> nul

	set "file_exist="
	if exist cronserver.pid set file_exist=0
	if exist runcherrypyserver.pid set file_exist=0
	if defined file_exist (
		echo -------------------------------------------------------------------
		echo KA Lite server is still running. 
		echo Please run stop.bat and then start.bat again.
		echo -------------------------------------------------------------------
		cd ..
		exit /b
	)

	reg query "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths" /f "python.exe" /s /k /e /d > nul
	if !ERRORLEVEL! EQU 1 (
		echo -------------------------------------------------------------------
    	echo Error: You do not seem to have Python installed.
    	echo Please install version 2.6 or 2.7, and re-run this script.
    	echo -------------------------------------------------------------------
		cd ..
		exit /b
	)

	echo Starting the cron server in the background.
	start /B runhidden.vbs "cronstart.bat"
	echo Running the web server in the background, on port %PORT%.
	start /B runhidden.vbs "serverstart.bat %PORT%"

	echo The server should now be accessible locally at: http://127.0.0.1:%PORT%/
	echo To access it from another connected computer, try the following:

	for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"IP Address"') do (
    	for /f "tokens=1 delims= " %%a in ("%%i") do echo http://%%a:%PORT%/
	)

) else (
	echo Please run install.bat first!
)
cd ..