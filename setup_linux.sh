#!/bin/bash
current_dir=`dirname "${BASH_SOURCE[0]}"`
SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )/scripts"
pyexec=`"$SCRIPT_DIR"/python.sh`

"$pyexec" "$current_dir/kalite/manage.py" setup

# TODO: make a check to see if we're running the rpi
we_are_rpi=""
if [[ $we_are_rpi = "True" ]]; then
    while true
    do
        echo
        echo "Do you wish to configure the Raspberry Pi optimizations for this server?"
        echo "You will need root/sudo privileges and an Internet connection."
        echo
        echo -n "Optimize now? [Y/N] "
        read CONFIRM
        case $CONFIRM in
            y|Y)
                echo "Optimize will start the KA Lite server now, "
                echo "    and automatically on every system boot."
                echo
                sudo "$SCRIPT_DIR/runatboot.sh"
                sudo "$SCRIPT_DIR/optimizerpi.sh"
                echo
                exit
                ;;
            n|N)
                echo "To optimize later, run ./scripts/optimizerpi.sh"
                echo
                break
                ;;
        esac
    done
fi

if [ -d "/etc/init.d" ]; then
    while true
    do
        echo
        echo "Do you wish to set the KA Lite server to run in the background automatically"
        echo -n "when you start this computer (you will need root/sudo privileges) [Y/N]? "
        read CONFIRM
        case $CONFIRM in
            y|Y)
                echo
                sudo "$SCRIPT_DIR/runatboot.sh"
                echo
                break
                ;;
            n|N)
                echo
                break
                ;;
        esac
    done
fi
