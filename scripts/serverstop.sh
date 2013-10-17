#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"
SERVER_STOPPED=true

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    if ! kill `cat "$KALITE_DIR/runcherrypyserver.pid"` > /dev/null 2>&1; then
        echo "We couldn't stop the server. Perhaps becoming root might help."
        SERVER_STOPPED=false
    fi
    rm "$KALITE_DIR/runcherrypyserver.pid"
else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi

