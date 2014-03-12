@echo off

rem have to change directory, in order to make sure we can import settings
set "OLD_DIR=%CD%"
set "SCRIPT_DIR=%~dp0"
set "KALITE_DIR=%SCRIPT_DIR%\..\kalite"

cd "%KALITE_DIR%"

if "%1" == "" (
  echo You must specify a setting
  set "SETTING="
) else (
  for /f %%a in ('start /b python.exe -c "import settings; print settings.%1"') do set "SETTING=%%a"
)

rem Set the value to a specified variable name
if "%2" == "" (
  set "%1=%SETTING%"
) else (
  set "%2=%SETTING%"
)
CD "%OLD_DIR%"