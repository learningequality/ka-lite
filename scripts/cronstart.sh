#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
pyexec=`"$SCRIPT_DIR/python.sh"`

pushd "$SCRIPT_DIR/../kalite" > /dev/null
pids=`ps aux | grep cronserver.py | grep -v "grep" | awk '{print $2}'`

if [ "$pids" ]; then
    echo "(Warning: Cron server may still be running; stopping old process ($pids) first)"
    kill $pids
fi

echo "Starting the cron server in the background."

"$pyexec" cronserver.py &
popd > /dev/null