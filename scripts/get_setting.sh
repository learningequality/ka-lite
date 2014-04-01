#!/bin/bash
pushd "$KALITE_DIR" > /dev/null
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

if [ "$1" == "" ]; then
    echo "You must specify a setting."
    exit 1
else
    "$pyexec" -c "import sys; sys.path += ['$KALITE_DIR', '$KALITE_DIR/../python-packages']; import settings; print settings.$1"
fi
popd > /dev/null
