#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"
pyexec=`"$SCRIPT_DIR/python.sh"`

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop pidfile=$KALITE_DIR/runcherrypyserver.pid
else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi
