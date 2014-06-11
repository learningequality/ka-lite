#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"

pyexec=`"$SCRIPT_DIR/python.sh"`

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    pid=`cat "$KALITE_DIR/runcherrypyserver.pid"`
    echo "(Warning: Web server may still be running; attempting to stop old process ($pid) first)"
    source "$SCRIPT_DIR/serverstop.sh"
fi

echo "Trying to start the web server."
"$pyexec" "$KALITE_DIR/manage.py" kaserve host=0.0.0.0 daemonize=true production=true pidfile="$KALITE_DIR/runcherrypyserver.pid"
rc=$?
if [[ $rc != 0 ]] ; then
    echo "Error: The web server was not started"
    exit $rc
fi
