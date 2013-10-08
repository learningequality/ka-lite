#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

"$pyexec" "$KALITE_DIR/manage.py" initdconfig > /etc/init.d/kalite
chmod 755 /etc/init.d/kalite
update-rc.d kalite defaults
