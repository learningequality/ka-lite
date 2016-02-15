#!/usr/bin/env bash

# Retrieve the exit code of the grep.
if [ -e "kalite/student_testing/models.py" ]; then
	echo "File found"
    exit 0
else
	echo "File not found"
    exit 1
fi