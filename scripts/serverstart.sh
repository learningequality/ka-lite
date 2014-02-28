#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR="$SCRIPT_DIR/../kalite"

pyexec=`"$SCRIPT_DIR/python.sh"`
port=`"$SCRIPT_DIR/get_setting.sh" PRODUCTION_PORT`
nthreads=`"$SCRIPT_DIR/get_setting.sh" CHERRYPY_THREAD_COUNT`

if [ -f "$KALITE_DIR/runcherrypyserver.pid" ];
then
    pid=`cat "$KALITE_DIR/runcherrypyserver.pid"`
    echo "(Warning: Web server may still be running; attempting to stop old process ($pid) first)"
    source "$SCRIPT_DIR/serverstop.sh"
fi

echo "Trying to start the web server on port $port."
"$pyexec" "$KALITE_DIR/manage.py" kaserve host=0.0.0.0 port=$port threads=$nthreads daemonize=true pidfile="$KALITE_DIR/runcherrypyserver.pid"
rc=$?
if [[ $rc != 0 ]] ; then
    echo "Error: The web server was not started"
    exit $rc
fi

echo "The server should now be accessible locally at: http://127.0.0.1:$port/"

ifconfig_path=`command -v ifconfig`
if [ "$ifconfig_path" == ""  ]; then
    ifconfig_path=`command -v /sbin/ifconfig`
fi
if [ "$ifconfig_path" ]; then
    echo "To access it from another connected computer, try the following address(es):"
    for ip in `"$ifconfig_path" | grep 'inet' | grep -oE '^[^0-9]+[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | grep -oE '[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+' | grep -v "127.0.0.1"`
    do
        echo http://$ip:$port/
    done
else
    echo "To access it from another connected computer, determine the external IP of this"
    echo "computer and append ':$port', so if the IP were 10.0.0.3, the url would then be:"
    echo "http://10.0.0.3:$port/"
fi
