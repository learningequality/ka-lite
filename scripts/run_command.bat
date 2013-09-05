# This file will run an arbitrary management command, within the confines of our "sandbox" script
for /f %%i in ("%0") do set curpath=%%~dpi 
start /b python.exe "%curpath%\manage.py" run_sandboxed_command