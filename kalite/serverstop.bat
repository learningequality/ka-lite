( set /p runcherrypyserverpid=<runcherrypyserver.pid ) > nul 2>&1
taskkill /f /pid %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
tskill %runcherrypyserverpid% > nul 2>&1 && echo CherryPy server was stopped!
del runcherrypyserver.pid > nul 2>&1