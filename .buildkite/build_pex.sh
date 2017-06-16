#!/usr/bin/env bash

set -euo pipefail

pip install pex                 # pex is really the only thing we need here.
buildkite-agent artifact download 'dist/ka_lite-*.whl' dist/
make pex
buildkite-agent artifact upload 'dist/*.pex'
