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

if [ `id -u` -eq 0 ]; then
	while true; do
		echo "-------------------------------------------------------------------"
		echo "You are installing KA-Lite as root user!"
		echo "Installing as root may cause some permission problems while running"
		echo "as a normal user in the future."
		echo "-------------------------------------------------------------------"
		echo
		read -p "Do you wish to continue and install it as root?" yn
		case $yn in
			[Yy]* ) break;;
			[Nn]* ) exit 1;;
			* ) echo "Please answer yes or no.";;
		esac
	done
fi

current_dir=`dirname "${BASH_SOURCE[0]}"`

# Platform-dependent use of stat (mac vs. non-mac)
if `uname -a | grep -q inux`; then
        current_dir_owner=`stat -c "%u" $current_dir`
else
        current_dir_owner=`stat -f "%u" $current_dir`
fi
 
# Check to see if the current user is the owner of the install directory
if [ ! `id -u` -eq $current_dir_owner ]; then
	echo "-------------------------------------------------------------------"
	echo "You are not the owner of this directory!"
	echo "Please copy all files to a directory that you own and then" 
	echo "re-run this script."
	echo "-------------------------------------------------------------------"
	exit 1
fi

if [ ! -w $current_dir/kalite ]; then
	echo "-------------------------------------------------------------------"
	echo "You do not have permission to write to this directory!"
	echo "-------------------------------------------------------------------"
	exit 1
fi

SCRIPT_DIR="$( cd "$( dirname "$0" )" && pwd )"
pyexec=`"$SCRIPT_DIR"/python.sh`
cd $current_dir/kalite

if [ -f "database/data.sqlite" ]; then
    echo "-------------------------------------------------------------------"
    echo "Error: Database file already exists! If this is a new installation,"
    echo "you should delete the file kalite/database/data.sqlite and then"
    echo "re-run this script. If the server is running, first run ./stop.sh"
    echo "-------------------------------------------------------------------"
    exit 1
fi

if [ $pyexec ]; then
    python_ver_ok=`$pyexec -c 'import sys; print(sys.version_info[0]==2 and sys.version_info[1] >= 5 and 1 or 0)'`
    if [[ $python_ver_ok != '1' ]]; then
        echo "----------------------------------------------------------------"
        echo "Error: You must have Python version 2.6.x or 2.7.x installed. Your version is:"
        $pyexec -V
        echo "----------------------------------------------------------------"
        exit 1
    fi
else    
    echo "----------------------------------------------------------------"
    echo "Error: You do not seem to have Python installed, or it is not on your path. Please install version 2.6 or 2.7, and re-run this script."
    echo "----------------------------------------------------------------"
    exit 1
fi    

echo "--------------------------------------------------------------------------------"
echo
echo "This script will configure the database and prepare it for use."
echo
echo "--------------------------------------------------------------------------------"
echo
read -n 1 -p "Press any key to continue..."
echo

$pyexec manage.py syncdb --migrate --noinput

# set the database permissions so that Apache will be able to access them
chmod 777 database
chmod 766 database/data.sqlite

echo
$pyexec manage.py generatekeys
echo

echo
echo "Please choose a username and password for the admin account on this device."
echo "You must remember this login information, as you will need to enter it to"
echo "administer this installation of KA Lite."
echo
$pyexec manage.py createsuperuser --email=dummy@learningequality.org
echo

hostname=`uname -n`
echo -n "Please enter a name for this server (or, press Enter to use '$hostname'): "
read -e name
if [ "$name" ]; then
    hostname=$name
fi
echo -n "Please enter a one-line description for this server (or, press Enter to leave blank): "
read -e description

# Look for an offline installation file
offline_install_file=static/data/zone_data.json
if [ ! -e "$offline_install_file" ]; then
    offline_install_file=
fi

$pyexec manage.py initdevice "$hostname" "$description" "$offline_install_file"

# Sync--we have a zone already.
$pyexec manage.py syncmodels


initd_available=`command -v update-rc.d`
if [ $initd_available ]; then
    while true
    do
        echo
        echo "Do you wish to set the KA Lite server to run in the background automatically"
        echo -n "when you start this computer (you will need root/sudo privileges) [Y/N]? "
        read CONFIRM
        case $CONFIRM in
            y|Y)
                echo
                sudo ./runatboot.sh
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

echo
echo "CONGRATULATIONS! You've finished installing the KA Lite server software."
echo "Please run './start.sh' to start the server, and then load the url"
echo "http://127.0.0.1:8008/ to complete the device configuration."
echo
