rem THIS STUFF IS FOR WINDOWS PPL
rem just call the environment's python

rem detect location
set "BIN_DIR=%~dp0"

reg add "hkcu\software\microsoft\command processor" /v Autorun /t reg_sz /d %BIN_DIR%/kalite.cmd