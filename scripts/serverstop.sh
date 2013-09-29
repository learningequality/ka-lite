#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    kill `cat "$KALITE_DIR/runcherrypyserver.pid"`
    rm "$KALITE_DIR/runcherrypyserver.pid"
else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi
