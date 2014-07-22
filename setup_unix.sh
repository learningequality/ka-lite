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

# Check if we have init.d for Linux or LaunchAgents for OSX so we can setup auto-start services.
if [ -d "/etc/init.d" ] || [ -d "/Library/LaunchAgents" ]; then
    while true
    do
        PLIST=/$HOME/Library/LaunchAgents/org.learningequality.kalite.plist
        echo
        echo "Do you wish to set the KA Lite server to run in the background automatically"
        echo -n "when you start this computer (you will need root/sudo privileges) [Y/N]? "
        read CONFIRM
        case $CONFIRM in
            y|Y)
                echo
                sudo "$SCRIPT_DIR/runatboot.sh"
                if [ -e $PLIST ]; then
                    launchctl load -w $PLIST
                    echo "KA Lite server will now run automatically on login."
                fi
                break
                ;;
            n|N)
                echo
                # Make sure we unload so plist doesn't run on login.  This might throw an
                # exception but cannot seem to suppress it even with a redirect to /dev/null
                # so we use the `launchctl list` to check if the plist is loaded.
                if [ -e $PLIST ]; then
                    plist_loaded=`launchctl list | grep org.learningequality.kalite`;
                    if [[ ! -z "$plist_loaded" ]]; then
                        launchctl unload -w $PLIST
                    fi
                fi
                break
                ;;
        esac
    done
fi
