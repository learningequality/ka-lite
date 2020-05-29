#!/usr/bin/env bash

set -euo pipefail

SCRIPTPATH=$(pwd)
PIP="$SCRIPTPATH/env/bin/pip"
PYTHON="$SCRIPTPATH/env/bin/python"

echo "Creating virtualenv..."
# This specifies 3.5 because of broken old server
virtualenv -p python3.5 env

$PIP freeze
$PIP install setuptools\<44
echo "Installing requirements..."
$PIP install -r requirements_pipeline.txt --upgrade

echo "Preparing artifact directories"
mkdir -p dist
mkdir -p installer

echo "Downloading artifacts..."
buildkite-agent artifact download 'dist/*.pex' dist/
buildkite-agent artifact download 'dist/*.whl' dist/
buildkite-agent artifact download 'dist/*.tar.gz' dist/
buildkite-agent artifact download 'installer/*.exe' installer/

echo "Executing upload script..."
$PYTHON .buildkite/upload_artifacts.py
