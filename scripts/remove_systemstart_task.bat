@echo off
TITLE Removing task to start KA Lite at system start
schtasks /delete /tn "KALite" & pause