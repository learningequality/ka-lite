@echo off

echo The stop command is not yet cleanly implemented for Windows.
echo To stop the server, we will have to kill all processes called "wscript.exe" and "python.exe".

:choice
set /P c=Do you wish to proceed [Y/N]?
if /I "%c%" EQU "Y" goto :yes
if /I "%c%" EQU "N" goto :somewhere_else
goto :choice

:yes
taskkill /f /im wscript.exe
taskkill /f /im python.exe
exit

:no
echo The server has not been stopped.