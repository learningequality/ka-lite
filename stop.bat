@echo off

echo The stop command is not yet cleanly implemented for Windows.
echo We will have to kill all processes called "python.exe".

:choice
set /P c=Do you wish to proceed [Y/N]?
if /I "%c%" EQU "Y" goto :yes
if /I "%c%" EQU "N" goto :no
goto :choice

:yes
taskkill /f /im python.exe
exit /B

:no
echo The server has not been stopped.