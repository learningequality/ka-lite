#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

UNAME=`uname`
if [ "$UNAME" == "Darwin" ]; then
    F=/$HOME/Library/LaunchAgents/org.learningequality.kalite.plist
    "$pyexec" "$KALITE_DIR/manage.py" initdconfig > "$F"
    chmod 644 "$F"
elif [ "$UNAME" == "Linux" ]; then
    "$pyexec" "$KALITE_DIR/manage.py" initdconfig > /etc/init.d/kalite
    chmod 755 /etc/init.d/kalite
    update-rc.d kalite defaults
fi
