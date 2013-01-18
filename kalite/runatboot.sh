#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
pyexec=`$SCRIPT_DIR/../python.sh`

$pyexec manage.py initdconfig > /etc/init.d/kalite
chmod 755 /etc/init.d/kalite
update-rc.d kalite defaults
