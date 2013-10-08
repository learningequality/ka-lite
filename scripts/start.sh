#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$SCRIPT_DIR/python.sh" ]; then
    KALITE_DIR=$SCRIPT_DIR/../kalite
else
    KALITE_DIR=$SCRIPT_DIR/kalite
    SCRIPT_DIR=$SCRIPT_DIR/scripts
fi

if [ ! -e "$KALITE_DIR/database/data.sqlite" ] ; then
	echo "Please run install.sh first!"
else
    # move any previously downloaded content from the old location to the new
	mv "$KALITE_DIR/static/videos/*" "$KALITE_DIR/../content" > /dev/null 2> /dev/null

	echo
	source "$SCRIPT_DIR/cronstart.sh"
	echo
	source "$SCRIPT_DIR/serverstart.sh"
fi
