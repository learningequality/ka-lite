#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

UNAME=`uname`
if [ "$UNAME" == "Darwin" ]; then
    echo "On Mac!"
    echo "Setting KA-Lite web server to run automatically on boot..."
#    F=/Library/LaunchAgents/org.learningequality.kalite.plist
#    "$pyexec" "$KALITE_DIR/manage.py" initdconfig > "$F"
#    chmod 644 "$F"
#    launchctl load -w "$F"
    "$pyexec" "$KALITE_DIR/manage.py" initdconfig > /Library/LaunchAgents/org.learningequality.kalite.plist
    chmod 644 /Library/LaunchAgents/org.learningequality.kalite.plist
    launchctl load -w /Library/LaunchAgents/org.learningequality.kalite.plist
    echo "done."
elif [ "$UNAME" == "Linux" ]; then
    echo "On Linux!"
    "$pyexec" "$KALITE_DIR/manage.py" initdconfig > /etc/init.d/kalite
    chmod 755 /etc/init.d/kalite
    update-rc.d kalite defaults
fi
