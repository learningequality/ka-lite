from django.core.management.base import BaseCommand, CommandError
import settings

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
        "%(project_path)s/../start.sh"
        ;;
    stop)
        echo "Shutting down ka-lite!"
        echo
        "%(project_path)s/../stop.sh"
        ;;
esac

"""

class Command(BaseCommand):
    help = "Print init.d startup script for the server daemon."

    def handle(self, *args, **options):
        self.stdout.write(script_template % {"project_path": settings.PROJECT_PATH})
