#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"

pyexec=`"$SCRIPT_DIR/python.sh"`
port=`"$SCRIPT_DIR/get_setting.sh" PRODUCTION_PORT`

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server id:" `cat "$KALITE_DIR/runcherrypyserver.pid"`
    echo "----------------------------------------------------------------"
    echo
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop pidfile="$KALITE_DIR/runcherrypyserver.pid"
    rc=$?
    if [[ $rc != 0 ]] ; then
        echo "Error when stopping the web server"
    fi

else
    echo "----------------------------------------------------------------"
    echo "Checking port" $port "and trying to close if a server is found"
    echo "----------------------------------------------------------------"    
    "$pyexec" "$KALITE_DIR/manage.py" runcherrypyserver stop host=0.0.0.0 port=$port
fi

