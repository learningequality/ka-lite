#!/usr/bin/env python

import os, signal

with open('runcherrypyserver.pid') as file:
    pid = int(file.readline().strip())
    os.kill(pid, signal.SIGTERM)
    os.remove('runcherrypyserver.pid')
