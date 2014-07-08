#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
KALITE_DIR=$SCRIPT_DIR/../kalite
pyexec=`"$SCRIPT_DIR/python.sh"`

"$pyexec" "$KALITE_DIR/manage.py" graph_models securesync main -g -o "$KALITE_DIR/model_graph.png"
if [ ! -e "$KALITE_DIR/model_graph.png" ]; then
    echo "Could not find expected output file: '$KALITE_DIR/model_graph.png"
else
    eog "$KALITE_DIR/model_graph.png"
    rm "$KALITE_DIR/model_graph.png"
fi
