"""
"""
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand
import getpass

script_template = """#!/bin/sh

# Author: Foundation for Learning Equality
#
# /etc/init.d/kalite

### BEGIN INIT INFO
# Provides:          kalite
# Required-Start:    $local_fs $remote_fs $network $syslog $named
# Required-Stop:
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: ka-lite daemon, a local Khan Academy content server
### END INIT INFO

set -e

. /lib/lsb/init-functions

case "$1" in
    start)
        # run ka-lite as another user, the one who generated this file
        su %(user)s -c "%(executable_path)s start"
        ;;
    stop)
        "%(executable_path)s" stop
        ;;
  restart)
    $0 stop
    sleep 1
    $0 start
    ;;
  status)
    "%(executable_path)s" status
    ;;
  *)
    log_success_msg "Usage: /etc/init.d/kalite {start|stop|restart|status}"
    exit 1
esac

"""

if sys.platform == 'darwin':
    # TODO(cpauya): Set the StandardOutPath key so that /dev/stdout or /dev/tty can be used.  Reason is if user runs:
    # `launchctl load -w $HOME/Library/LaunchAgents/org.learningequality.kalite.plist`
    # then the output of `kalite start` are not shown on the terminal but instead on
    # `/tmp/kalite.out`.  There must be a way to set it to display on the user's terminal.
    script_template = """
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>org.learningequality.kalite</string>
        <key>Program</key>
        <string>%(executable_path)s start</string>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/tmp/kalite.out</string>
        <key>StandardErrorPath</key>
        <string>/tmp/kalite.err</string>
        <key>WorkingDirectory</key>
        <string>%(cwd)s</string>
    </dict>
</plist>
    """


class Command(BaseCommand):
    help = "Print init.d startup script for the server daemon."

    def handle(self, *args, **options):
        if settings.IS_SOURCE:
            executable_path = os.path.abspath(os.path.join(settings.PROJECT_PATH, "..", "bin", "kalite"))
            cwd = settings.PROJECT_PATH
        else:
            executable_path = "kalite"
            cwd = "/"
        
        self.stdout.write(
            script_template % {
                "executable_path": executable_path,
                "cwd": cwd,
                "user": getpass.getuser(),
            }
        )
