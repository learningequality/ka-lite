@echo off
set "SCRIPT_DIR=%~dp0"

TITLE Adding task to start KA Lite at system start
schtasks /create /tn "KALite" /tr "%SCRIPT_DIR%\start.bat" /sc onstart & pause