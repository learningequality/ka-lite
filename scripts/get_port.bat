rem have to change directory, in order to make sure we can import settings
set OLD_DIR=%CD%
set SCRIPT_DIR=%~dp0
cd "%SCRIPT_DIR%\..\kalite"

if "%1" == "" (
  for /f %%a in ('start /b python.exe -c "import settings; print settings.PRODUCTION_PORT"') do set PORT=%%a
) else (
  set PORT=%1
)

CD "%OLD_DIR%"