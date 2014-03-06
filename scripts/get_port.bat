rem have to change directory, in order to make sure we can import settings
@echo off
set "SCRIPT_DIR=%~dp0"

if "%1" == "" (
  CALL "%SCRIPT_DIR%\get_setting.bat" PRODUCTION_PORT PORT
) else (
  set "PORT=%1"
)
