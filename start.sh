#!/bin/bash

cd `dirname "${BASH_SOURCE[0]}"`/kalite

if [ -f "database/data.sqlite" ] ; then
	
    # move any previously downloaded content from the old location to the new
	mv static/videos/* ../content > /dev/null 2> /dev/null

	echo
	source cronstart.sh
	echo
	source serverstart.sh
else
	echo "Please run install.sh first!"
fi

cd ..
