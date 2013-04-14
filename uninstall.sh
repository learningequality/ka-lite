#!/bin/bash

current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ ! `id -u` -eq `stat -c "%u" $current_dir` ]; then
	echo "-------------------------------------------------------------------"
	echo "You are not the owner of this directory!"
	echo "We don't think it's a good idea to uninstall something you"
        echo "do not own."
	echo "-------------------------------------------------------------------"
	exit 1
fi

if [ ! -w $current_dir/kalite ]; then
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
                echo "You are about to remove the service which started KA Lite server"
                echo "in the background (this will require root/sudo privileges)"
                sudo $current_dir/kalite/donotrunatboot.sh

                rm -rf $current_dir

                echo "Thank you for flying with KA Lite!"
                ;;
        n|N)
                echo
                break
                ;;
esac
exit 1
