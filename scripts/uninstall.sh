#!/bin/bash

echo "  _   __  ___    _     _ _        "
echo " | | / / / _ \  | |   (_) |       "
echo " | |/ / / /_\ \ | |    _| |_ ___  "
echo " |    \ |  _  | | |   | | __/ _ \ "
echo " | |\  \| | | | | |___| | ||  __/ "
echo " \_| \_/\_| |_/ \_____/_|\__\___| "
echo "                                  "
echo "http://kalite.learningequality.org"
echo "                                  "

SCRIPT_DIR=`dirname "${BASH_SOURCE[0]}"`
if [ -e $SCRIPT_DIR/kalite ];; then
    BASE_DIR=$SCRIPT_DIR
else
    BASE_DIR=$SCRIPT_DIR/..
fi
KALITE_DIR=$BASE_DIR/kalite

if [ ! `id -u` -eq `stat -c "%u" "$KALITE_DIR"` ]; then
        echo "-------------------------------------------------------------------"
        echo "You are not the owner of this directory!"
        echo "We don't think it's a good idea to uninstall something you"
        echo "do not own."
        echo "-------------------------------------------------------------------"
        exit 1
fi

if [ ! -w "KALITE_DIR" ]; then
        echo "-------------------------------------------------------------------"
        echo "You do not have permission to write to this directory!"
        echo "Thus, it's not possible to remove it =)"
        echo "-------------------------------------------------------------------"
        exit 1
fi

echo
echo -n "Do you wish to remove the KA Lite server and all downloaded files? [Y/N]"
read CONFIRM

case $CONFIRM in 
        y|Y)
                "$SCRIPT_DIR/stop.sh"
                echo "You are about to remove the service which started KA Lite server"
                echo "in the background (this will require root/sudo privileges)"
                sudo "$KALITE_DIR/donotrunatboot.sh

                rm -rf "$BASE_DIR"

                echo "Thank you for flying with KA Lite!"
                ;;
        n|N)
                echo
                break
                ;;
esac
exit 1
