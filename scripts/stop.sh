#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
if [ ! -e "$SCRIPT_DIR/serverstop.sh" ]; then
    SCRIPT_DIR=$SCRIPT_DIR/scripts
fi

source "$SCRIPT_DIR/serverstop.sh"
source "$SCRIPT_DIR/cronstop.sh"
