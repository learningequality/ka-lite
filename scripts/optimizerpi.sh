#!/bin/bash

current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/python.sh" ]; then
    KALITE_DIR=$current_dir/../kalite
else
    KALITE_DIR=$current_dir/kalite
fi

we_are_rpi=`"$current_dir/get_setting.sh" package_selected\(\"RPi\"\)`
if [ $we_are_rpi != "True" ]; then
    echo "Error: we aren't configured as a Raspberry Pi, cannot continue"
    read WAITING
    exit
fi

echo "Step 1 - Installing M2Crypto, psutil and nginx"

# discover if packages are already installed
to_install=""
python -c "import M2Crypto" >/dev/null 2>&1
if [ $? != 0 ] ; then to_install="python-m2crypto"; fi
python -c "import psutil" >/dev/null 2>&1
if [ $? != 0 ] ; then to_install="$to_install python-psutil"; fi
nginx -v >/dev/null 2>&1
if [ $? != 0 ] ; then to_install="$to_install nginx"; fi

# check network (by trying some likely sites), but only if packages need installing
if [ "$to_install" != "" ] ; then
    echo "Info: Need to install: $to_install, testing connection"
    wget -q http://adhocsync.org >/dev/null 2>&1
    if [ $? != 0 ] ; then wget -q http://mirrordirector.raspbian.org >/dev/null 2>&1
        if [ $? != 0 ] ; then wget -q http://google.com >/dev/null 2>&1
            if [ $? != 0 ] ; then
                echo "Error: internet connection isn't working, cannot continue"
                read WAITING
                exit 1
            fi
        fi
    fi
else
    echo "Info: Everything is already installed"
fi

if [ "$to_install" != "" ] ; then sudo apt-get -y install $to_install; fi

# Finally, check the packages are installed, incase there was an apt-get failure
sanity_check_ok="False"
python -c "import M2Crypto" >/dev/null 2>&1
if [ $? = 0 ] ; then python -c "import psutil" >/dev/null 2>&1
    if [ $? = 0 ] ; then nginx -v >/dev/null 2>&1
        if [ $? = 0 ] ; then sanity_check_ok="True"; fi
    fi
fi

if [ $sanity_check_ok != "True" ] ; then
    echo "Error: One or more modules are missing, cannot continue"
    read WAITING
    exit 1
fi

echo "Step 2 - Configure or reconfigure nginx to work with KA Lite"

if [ -f /etc/nginx/sites-enabled/default ]; then
    sudo rm /etc/nginx/sites-enabled/default 
fi
if [ -f /etc/nginx/sites-enabled/kalite ]; then
    sudo rm /etc/nginx/sites-enabled/kalite
fi

sudo touch /etc/nginx/sites-available/kalite 
sudo sh -c "$KALITE_DIR/manage.py nginxconfig > /etc/nginx/sites-available/kalite" 
sudo ln -s /etc/nginx/sites-available/kalite /etc/nginx/sites-enabled/kalite

echo "Step 3 - Optimize nginx configuration"

sudo rm /etc/nginx/nginx.conf
sudo touch /etc/nginx/nginx.conf

sudo sh -c "cat > /etc/nginx/nginx.conf" <<'NGINX'
user www-data;
pid /var/run/nginx.pid;

###
# we have 1 cpu so only need 1 worker process
worker_processes 1;

events {
    ###
    # good overall speed on RPi with this setting
    worker_connections 1536;

    ###
    # Activate the optimised polling for linux 
    use epoll;

    ###
    # Keep multi_accept off - RPi+KA Lite is slowed if "on"
    multi_accept off;
}

http {
    ###
    # RPi+KA Lite is faster with sendfile "off"
    sendfile off;
    tcp_nopush off;

    tcp_nodelay on;
    keepalive_timeout 65;
    types_hash_max_size 2048;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    ###
    # Speed up landing page by caching open file descriptors
    open_file_cache max=2048;

    ##
    # Logging Settings
    # don't log, we don't need to know normally
    access_log off;
    error_log off;

    ##
    # Gzip Settings
    # We are CPU limited, not bandwidth limited, so don't gzip
    gzip off;

    ##
    # Virtual Host Configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}

NGINX

echo 'Step 4 - Finally... stopping and starting the background servers'

sudo service kalite stop
sudo service kalite start
sudo service nginx stop
sudo service nginx start

echo 'Now you can access KA-Lite through port 8008 (which will use optimizations)'
echo 'or directly through port 7007 (which will not use optimizations)'
