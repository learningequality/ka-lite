@echo off

rem determine the script directory (could be in scripts, could be in root folder)
set "SCRIPT_DIR=%~dp0"

if exist "%SCRIPT_DIR%\python.bat" (
    set "KALITE_DIR=%SCRIPT_DIR%\..\kalite"
) else (
    set "SCRIPT_DIR=%SCRIPT_DIR%\scripts"
    set "KALITE_DIR=%SCRIPT_DIR%\kalite"
)

call "%SCRIPT_DIR%\get_port.bat" %*

if not exist "%KALITE_DIR%\database\data.sqlite" (
    echo Please run install.bat first!
) else (
    REM transfer any previously downloaded content from the old location to the new
    move "%KALITE_DIR%\static\videos\*" "%KALITE_DIR%\..\content" > nul 2> nul

    set "file_exist="
    if exist "%KALITE_DIR%\cronserver.pid" set file_exist=0
    if exist "%KALITE_DIR%\runcherrypyserver.pid" set file_exist=0
    if defined file_exist (
        echo -------------------------------------------------------------------
        echo KA Lite server is still running.
        echo Please run stop.bat and then start.bat again.
        echo -------------------------------------------------------------------
        exit /b
    )

    call "%SCRIPT_DIR%\python.bat"
    if !ERRORLEVEL! EQU 1 (
        echo -------------------------------------------------------------------
        echo Error: You do not seem to have Python installed.
        echo Please install version 2.6 or 2.7, and re-run this script.
        echo -------------------------------------------------------------------
        exit /b
    )

    CALL "%SCRIPT_DIR%\get_setting.bat" CENTRAL_SERVER CENTRAL_SERVER
    if "%CENTRAL_SERVER%" EQU "False" (
        echo Starting the cron server in the background.
        call "%SCRIPT_DIR%\cronstart.bat"
    )
    echo Running the web server in the background, on port %PORT%.
    call "%SCRIPT_DIR%\serverstart.bat"

    echo The server should now be accessible locally at: http://127.0.0.1:%PORT%/
    echo To access it from another connected computer, try the following:

    for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /R /C:"IPv4 Address" /C:"IP Address"') do (
        for /f "tokens=1 delims= " %%a in ("%%i") do echo http://%%a:%PORT%/
    )
)