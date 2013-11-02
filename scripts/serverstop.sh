#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"
pyexec=`"$SCRIPT_DIR/python.sh"`
SERVER_STOPPED=true

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop pidfile=$KALITE_DIR/runcherrypyserver.pid
    rc=$?
    if [[ $rc != 0 ]] ; then
        echo "We couldn't stop the server. Perhaps becoming root might help."
        SERVER_STOPPED=false
    fi

else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi

