#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

pids=`ps aux | grep cronserver | grep manage | grep -v "grep" | awk '{print $2}'`

if [ "$pids" ]; then
    echo "(Warning: Cron server may still be running; stopping old process ($pids) first)"
    source "$SCRIPT_DIR/cronstop.sh"
fi

freq=`"$SCRIPT_DIR/get_setting.sh" CRONSERVER_FREQUENCY`
"$pyexec" "$KALITE_DIR/manage.py" cronserver "$freq" &
