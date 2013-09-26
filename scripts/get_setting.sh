#!/bin/bash
SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

pushd "$KALITE_DIR" > /dev/null
if [ "$1" == "" ]; then
    echo "You must specify a setting."
    exit 1
else
    "$pyexec" -c "import settings; print settings.$1"
fi
popd > /dev/null