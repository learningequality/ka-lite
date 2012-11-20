#!/bin/bash

cd kalite

if [ -f "database/data.sqlite" ]; then
    echo "----------------------------------------------------------------"
    echo "Error: Database file already exists! If this is a new installation, you should delete the file kalite/data.sqlite and then re-run this script."
    echo "----------------------------------------------------------------"
    exit 1
fi

python_installed=`command -v python`
if [ $python_installed ]; then
    python_ver_ok=`python -c 'import sys; print(sys.version_info[0]==2 and sys.version_info[1] >= 5 and 1 or 0)'`
    if [ $python_ver_ok != '1' ]; then
        echo "----------------------------------------------------------------"
        echo "Error: You must have Python version 2.5.x, 2.6.x, or 2.7.x installed. Your version is:"
        python -V
        echo "----------------------------------------------------------------"
        exit 1
    fi
else    
    echo "----------------------------------------------------------------"
    echo "Error: You do not seem to have Python installed, or it is not on your path. Please install version 2.5, 2.6, or 2.7, and re-run this script."
    echo "----------------------------------------------------------------"
    exit 1
fi    

echo "----------------------------------------------------------------"
echo
echo "This script will configure the database and prepare it for use."
echo
echo "When asked if you want to create a superuser, type 'yes' and enter your details."
echo "You must remember this login information, as you will need to enter it to administer the website."
echo
echo "----------------------------------------------------------------"
echo
read -n 1 -p "Press any key to continue..."

python manage.py syncdb --migrate

# set the database permissions so that Apache will be able to access them
chmod 777 database
chmod 766 database/data.sqlite

