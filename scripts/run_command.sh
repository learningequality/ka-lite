#!/bin/bash
# This file will run an arbitrary management command, within the confines of our "sandbox" script
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$SCRIPT_DIR/kalite" ]; then
    KALITE_DIR=$SCRIPT_DIR/kalite
    SCRIPT_DIR=$SCRIPT_DIR/scripts
else
    KALITE_DIR=$SCRIPT_DIR/../kalite
fi

pyexec=`"$SCRIPT_DIR/python.sh"`
"$pyexec" "$KALITE_DIR/manage.py" run_sandboxed_command $~