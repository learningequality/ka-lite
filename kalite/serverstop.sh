#!/bin/bash

cd `dirname "${BASH_SOURCE[0]}"`
if [ -f "runcherrypyserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    kill `cat runcherrypyserver.pid`
    rm runcherrypyserver.pid
else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi
