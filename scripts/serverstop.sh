#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"

pyexec=`"$SCRIPT_DIR/python.sh"`

PIDFILE="$KALITE_DIR/runcherrypyserver.pid"
if [ -f $PIDFILE ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server id:" `cat "$KALITE_DIR/runcherrypyserver.pid"`
    echo "----------------------------------------------------------------"
    echo
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop pidfile=$PIDFILE
    rc=$?
    if [[ $rc != 0 ]] ; then
        echo "Error when stopping the web server"
    fi

else
    echo "----------------------------------------------------------------"
    echo "Checking port to close if a server is found"
    echo "----------------------------------------------------------------"
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop host=0.0.0.0 pidfile=$PIDFILE
fi
