@echo off

set "SCRIPT_DIR=%~dp0"
set "KALITE_DIR=%SCRIPT_DIR%..\kalite"

if exist "%KALITE_DIR%\cronserver.pid" (
    rem have to change directory, in order to make sure we can access pid files
    set "CURRENT_DIR=%CD%"
    cd "%KALITE_DIR%"

    for /f "tokens=*" %%i in ( cronserver.pid ) do (
        taskkill /f /pid %%i > nul 2>&1 && echo Cron server was stopped!
        tskill %%i > nul 2>&1 && echo Cron server was stopped!
    )
    del cronserver.pid > nul 2>&1
    cd "%CURRENT_DIR%"
)