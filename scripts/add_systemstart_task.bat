@echo off
TITLE Adding task to start KA Lite at system start
schtasks /create /tn "KALITE" /tr %CD%\start.bat /sc onstart & exit