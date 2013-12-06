@echo off

rem have to change directory, in order to make sure we can access pid files
set SCRIPT_DIR=%~dp0
set KALITE_DIR=%SCRIPT_DIR%\..\kalite
set CURRENT_DIR=%CD%
cd "%KALITE_DIR%"

if exist "%KALITE_DIR%\cronserver.pid" (
    for /f "tokens=*" %%i in (cronserver.pid) do (
        taskkill /f /pid %%i > nul 2>&1 && echo Cron server was stopped!
        tskill %%i > nul 2>&1 && echo Cron server was stopped!
        del "%KALITE_DIR%\cronserver.pid" > nul 2>&1
        cd "%CURRENT_DIR%"
    )
)