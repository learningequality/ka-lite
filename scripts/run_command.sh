#!/bin/bash
# This file will run an arbitrary management command, within the confines of our "sandbox" script
current_dir=`dirname "${BASH_SOURCE[0]}"`
source "$current_dir/python.sh"
$PYEXEC "$current_dir/kalite/manage.py" run_sandboxed_command