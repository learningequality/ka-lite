#!/bin/bash

PYEXEC=`command -v python2`
if [[ ! -e $PYEXEC ]]; then
    PYEXEC=`command -v python` 
fi
echo $PYEXEC
