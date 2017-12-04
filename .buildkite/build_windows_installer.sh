#!/usr/bin/env bash

set -euo pipefail

PARENT_PATH=$(pwd)
KALITE_DOCKER_PATH="$PARENT_PATH/windows_installer_docker_build"
KALITE_WINDOWS_PATH="$KALITE_DOCKER_PATH/ka-lite-installers/windows"

# Download artifacts to dist/
mkdir -p dist
buildkite-agent artifact download 'dist/*.whl' dist/
make dockerwriteversion

# Clone KA-Lite windows installer and download content pack
cd $KALITE_DOCKER_PATH
git clone https://github.com/learningequality/ka-lite-installers.git && cd ka-lite-installers && git checkout 0.17.x
cd $KALITE_WINDOWS_PATH && wget http://pantry.learningequality.org/downloads/ka-lite/0.17/content/contentpacks/en.zip

# Copy kalite whl files to kalite windows installer path
COPY_CMD="cp $PARENT_PATH/dist/*.whl $KALITE_WINDOWS_PATH"
$COPY_CMD

if [ $? -ne 0 ]; then
    echo "... Abort! Error running $COPY_CMD"
    exit 1
fi

# Build KA-Lite windows installer docker image
KALITE_BUILD_VERSION=$(cat $PARENT_PATH/kalite/VERSION)
cd $KALITE_DOCKER_PATH
DOCKER_BUILD_CMD="docker image build -t $KALITE_BUILD_VERSION-build ."
$DOCKER_BUILD_CMD

if [ $? -ne 0 ]; then
    echo "... Abort! Error running $DOCKER_BUILD_CMD."
    exit 1
fi

INSTALLER_PATH="$KALITE_DOCKER_PATH/installer"
mkdir -p $INSTALLER_PATH

# Run KA-Lite windows installer docker image.
DOCKER_RUN_CMD="docker run -v $INSTALLER_PATH:/installer/ $KALITE_BUILD_VERSION-build"
$DOCKER_RUN_CMD

if [ $? -ne 0 ]; then
    echo "... Abort! Error running $DOCKER_RUN_CMD."
    exit 1
fi
cd $KALITE_DOCKER_PATH
buildkite-agent artifact upload './installer/*.exe'
