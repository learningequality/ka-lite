rem THIS STUFF IS FOR WINDOWS PPL
rem just call the environment's python

rem detect location
set "BIN_DIR=%~dp0"

reg add "HKEY_CURRENT_USER\Software\Microsoft\Command Processor" /v Autorun /t reg_sz /d "%BIN_DIR%kalite.cmd"