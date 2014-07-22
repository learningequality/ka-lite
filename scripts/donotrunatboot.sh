#!/bin/bash
UNAME=`uname`
if [ "$UNAME" == "Darwin" ]; then
    echo "On Mac!"
    echo "Removing setting for KA-Lite web server to run automatically on boot..."
    F=/Library/LaunchAgents/org.learningequality.kalite.plist
    launchctl unload -w "$F"
    echo "done."
elif [ "$UNAME" == "Linux" ]; then
    echo "On Linux!"
    update-rc.d -f kalite remove
fi
