#!/bin/bash

cd `dirname "${BASH_SOURCE[0]}"`
if [ -f "runwsgiserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Closing server instance."
    echo "----------------------------------------------------------------"
    echo
    kill `cat runwsgiserver.pid`
    rm runwsgiserver.pid
else
    echo "----------------------------------------------------------------"
    echo "Server does not appear to be running."
    echo "----------------------------------------------------------------"    
fi
