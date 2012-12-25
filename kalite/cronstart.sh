#!/bin/bash

pyexec=`../python.sh`

cd `dirname "${BASH_SOURCE[0]}"`
pids=`ps aux | grep cronserver.py | grep -v "grep" | awk '{print $2}'`

if [ "$pids" ]; then
    echo "(Warning: Cron server may still be running; stopping old process ($pids) first)"
    kill $pids
fi

echo "Starting the cron server in the background."

$pyexec cronserver.py &
