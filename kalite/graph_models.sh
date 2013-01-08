#!/bin/bash

pyexec=`../python.sh`

cd `dirname "${BASH_SOURCE[0]}"`
$pyexec manage.py graph_models securesync main -g -o model_graph.png
eog model_graph.png
rm model_graph.png
