#!/bin/bash
UNAME=`uname`
if [ "$UNAME" == "Darwin" ]; then
    echo "Removing setting for KA-Lite web server to run automatically on login..."
    F=/$HOME/Library/LaunchAgents/org.learningequality.kalite.plist
    launchctl unload -w "$F"
    echo "done."
elif [ "$UNAME" == "Linux" ]; then
    update-rc.d -f kalite remove
fi
