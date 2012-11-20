if [ -f "runwsgiserver.pid" ];
then
    pid=`cat runwsgiserver.pid`
    echo "(Warning: Web server may still be running; stopping old process ($pid) first)"
    kill $pid
    rm runwsgiserver.pid
fi

echo "Running the web server on port 8008."
python manage.py runwsgiserver host=0.0.0.0 port=8008 threads=50 daemonize=true pidfile=runwsgiserver.pid
