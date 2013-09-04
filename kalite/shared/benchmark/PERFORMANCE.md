## Raspberry Pi performance tuning

*Initial version 1 by Gimick*

Performance of the Raspberry Pi server can be significantly improved with these configuration changes:


**Changes to local_settings.py**

```
echo "#NGINX is on port 8008 and expects ka-lite on port 7007" >> ~/ka-lite/kalite/local_settings.py
echo "PRODUCTION_PORT=7007" >> ~/ka-lite/kalite/local_settings.py
echo "" >> ~/ka-lite/kalite/local_settings.py
echo "#Persist ka-lite django page cache between reboots" >> ~/ka-lite/kalite/local_settings.py
echo "CACHE_LOCATION = '/var/tmp/kalite/cache'" >> ~/ka-lite/kalite/local_settings.py
echo "" >> ~/ka-lite/kalite/local_settings.py
echo "#Optimise cherrypy server for Raspberry Pi" >> ~/ka-lite/kalite/local_settings.py
echo "CHERRYPY_THREAD_COUNT = 20" >> ~/ka-lite/kalite/local_settings.py
echo "" >> ~/ka-lite/kalite/local_settings.py

```

**Use NGINX as a proxy for static files**

```

sudo apt-get install nginx
sudo rm /etc/nginx/sites-enabled/default
sudo touch /etc/nginx/sites-enabled/kalite
sudo sh -c 'ka-lite/kalite/manage.py nginxconfig > /etc/nginx/sites-enabled/kalite'
sudo rm /etc/nginx/nginx.conf
sudo nano /etc/nginx/nginx.conf 

```

paste this configuration into the nginx.conf file

```
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
	# Keep multi_accept off - RPi+kalite is slowed if "on"
	multi_accept off;
}

http {
	###
	# RPi+kalite "off" is a faster with sendfile "off"
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

```

**Finally, reboot**

```
sudo reboot

```
