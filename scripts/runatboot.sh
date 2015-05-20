#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
BASE_DIR=$SCRIPT_DIR/..
pyexec=`"$SCRIPT_DIR/python.sh"`

UNAME=`uname`
if [ "$UNAME" == "Darwin" ]; then
    F=/$HOME/Library/LaunchAgents/org.learningequality.kalite.plist
    "$pyexec" "$BASE_DIR/bin/kalite" manage initdconfig > "$F"
    chmod 644 "$F"
elif [ "$UNAME" == "Linux" ]; then
    "$pyexec" "$BASE_DIR/bin/kalite" manage initdconfig > /etc/init.d/kalite
    chmod 755 /etc/init.d/kalite
    update-rc.d kalite defaults
fi
