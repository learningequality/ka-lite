rem have to change directory, in order to make sure we can import settings
set SCRIPT_DIR=%~dp0

if "%1" == "" (
  for /f %%a in ('"%SCRIPT_DIR\get_setting.bat" PRODUCTION_PORT') do set PORT=%%a
) else (
  set PORT=%1
)
