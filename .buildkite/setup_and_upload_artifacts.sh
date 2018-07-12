#!/usr/bin/env bash

set -euo pipefail

SCRIPTPATH=$(pwd)
PIP="$SCRIPTPATH/env/bin/pip"
PYTHON="$SCRIPTPATH/env/bin/python"

echo "Creating virtualenv..."
virtualenv -p python3 env

echo "Installing requirements..."
$PIP install -r requirements_pipeline.txt

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
