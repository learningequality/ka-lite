#!/bin/bash

current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/python.sh" ]; then
    KALITE_DIR=$current_dir/../kalite
else
    KALITE_DIR=$current_dir/kalite
fi

echo "Step 1. -- change KA Lite local_settings.py"

echo 'CONFIG_PACKAGE = "RPi"' >> $KALITE_DIR/local_settings.py

echo "Step 2 - Install nginx and Configure to work with KA Lite"

sudo apt-get -y install nginx 
sudo rm /etc/nginx/sites-enabled/default 
sudo touch /etc/nginx/sites-enabled/kalite 
sudo sh -c "$KALITE_DIR/manage.py nginxconfig > /etc/nginx/sites-enabled/kalite" 

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
    gzip on;
    gzip_disable "msie6";

    ##
    # Virtual Host Configs
    include /etc/nginx/conf.d/*.conf;
    include /etc/nginx/sites-enabled/*;
}

NGINX

echo 'Step 4 - Finally'

sudo service kalite stop
sudo service kalite start
sudo service nginx stop
sudo service nginx start

echo 'Now you can access KA-Lite through port 8008 (which will use optimizations)'
echo 'or directly through port 7007 (which will not use optimizations)'
