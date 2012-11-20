cd kalite

if [ -f "runwsgiserver.pid" ];
then
    echo "----------------------------------------------------------------"
    echo "Server may still be running; stopping the old instance first."
    kill `cat runwsgiserver.pid`
    rm runwsgiserver.pid
fi

echo "----------------------------------------------------------------"
echo "Running the server on port 8008."
echo "----------------------------------------------------------------"
python manage.py runwsgiserver port=8008 daemonize=true pidfile=runwsgiserver.pid
