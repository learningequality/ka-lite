#!/usr/bin/env bash

KA_LITE_DIR="/kalite"
SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
WORKING_DIR="$SCRIPTPATH/temp"
CP_DEBIAN_FOLDER="cp -R /kalite/ka-lite-installers/debian/debian /kalite/debian"
DEBUILD_CMD="debuild -b -us -uc"
COLLECT_DEB_MV="mv /*.deb /kalitedist"

STEP=0
STEPS=6

echo "$STEP/$STEPS. Checking if requirements are installed..."
$CP_DEBIAN_FOLDER
if [ $? -ne 0 ]; then
    echo ".. Abort!  Error/s encountered '$CP_DEBIAN_FOLDER'..."
    exit 1
fi

((STEP++))
echo "$STEP/$STEPS. Running 'setup.py install --static'..."

cd "$KA_LITE_DIR"
SETUP_CMD="python setup.py install"
SETUP_STATIC_CMD="$SETUP_CMD --static"
echo ".. Running $SETUP_STATIC_CMD..."
$SETUP_STATIC_CMD
if [ $? -ne 0 ]; then
    echo ".. Abort!  Error/s encountered running '$SETUP_STATIC_CMD'."
    exit 1
fi

cd "$KA_LITE_DIR"
mk-build-deps -i -r -t 'apt-get -y' debian/control
if [ $? -ne 0 ]; then
    echo ".. Abort!  Error/s encountered running 'mk-build-deps'."
    exit 1
fi

((STEP++))
echo "$STEP/$STEPS. Now Running  '$DEBUILD_CMD'..."

cd "$KA_LITE_DIR"
$DEBUILD_CMD
if [ $? -ne 0 ]; then
    echo ".. Abort!  Error/s encountered running '$DEBUILD_CMD'."
    exit 1
fi

$COLLECT_DEB_MV
if [ $? -ne 0 ]; then
    echo ".. Abort!  Error/s encountered running '$WORKING_DIR/$DEB_INSTALLER_DIR'."
    exit 1
fi