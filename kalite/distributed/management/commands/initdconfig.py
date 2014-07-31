"""
"""
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

script_template = """
#! /bin/sh

# Author: Jamie Alexandre, 2012
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

case "$1" in
    start)
        echo "Starting ka-lite!"
        #run ka-lite as the owner of the project folder, and not as root
        su `stat --format="%%U" "%(repo_path)s"` -c "%(script_path)s/start.sh"
        ;;
    stop)
        echo "Shutting down ka-lite!"
        echo
        "%(script_path)s/stop.sh"
        ;;
esac

"""

if sys.platform == 'darwin':
    # TODO(cpauya): Set the StandardOutPath key so that /dev/stdout or /dev/tty can be used.  Reason is if user runs:
    # `launchctl load -w $HOME/Library/LaunchAgents/org.learningequality.kalite.plist`
    # then the output of the `start.sh` script are not shown on the terminal but instead on
    # `/tmp/kalite.out`.  There must be a way to set it to display on the user's terminal.
    script_template = """
<?xml version="1.0" encoding="UTF-8" ?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>org.learningequality.kalite</string>
        <key>Program</key>
        <string>%(script_path)s/start.sh</string>
        <key>RunAtLoad</key>
        <true/>
        <key>StandardOutPath</key>
        <string>/tmp/kalite.out</string>
        <key>StandardErrorPath</key>
        <string>/tmp/kalite.err</string>
        <key>WorkingDirectory</key>
        <string>%(script_path)s</string>
    </dict>
</plist>
    """


class Command(BaseCommand):
    help = "Print init.d startup script for the server daemon."

    def handle(self, *args, **options):
        repo_path = os.path.join(settings.PROJECT_PATH, "..")
        script_path = os.path.join(repo_path, "scripts")
        self.stdout.write(script_template % {"repo_path": repo_path, "script_path": script_path})
