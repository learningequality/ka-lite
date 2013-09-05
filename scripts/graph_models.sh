#!/bin/bash

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
pyexec=`$SCRIPT_DIR/../python.sh`

cd "$SCRIPT_DIR"
$pyexec manage.py graph_models securesync main -g -o model_graph.png
eog model_graph.png
rm model_graph.png
