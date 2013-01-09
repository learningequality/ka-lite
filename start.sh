#!/bin/bash
cd kalite
if [ -f "database/data.sqlite" ] ; then
	echo
	./cronstart.sh
	echo
	./serverstart.sh
else
	echo "Please run install.sh first!"
fi
cd ..
