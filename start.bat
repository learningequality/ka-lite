@echo off
cd kalite
echo.
start /B runhidden.vbs "cronstart.bat"
echo.
start /B runhidden.vbs "serverstart.bat"
cd ..