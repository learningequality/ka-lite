/ka-lite/kalite/cronstart.sh

# /ka-lite/kalite/serverstart.sh

cd /ka-lite/kalite

# python manage.py runcherrypyserver host=0.0.0.0 port=8008 threads=50 daemonize=true pidfile=runcherrypyserver.pid

python manage.py runserver 0.0.0.0:8000
