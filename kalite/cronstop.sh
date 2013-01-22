#!/bin/bash

pids=`ps aux | grep cronserver.py | grep -v "grep" | awk '{print $2}'`

if [ "$pids" ]; then
    echo "----------------------------------------------------------------"
    echo "Killing all existing cron server processes ($pids)."
    echo "----------------------------------------------------------------"
    kill $pids
else
    echo "----------------------------------------------------------------"
    echo "Cron server does not seem to be running."
    echo "----------------------------------------------------------------"
fi
