cd `dirname "${BASH_SOURCE[0]}"`
if [ -f "runwsgiserver.pid" ];
then
    pid=`cat runwsgiserver.pid`
    echo "(Warning: Web server may still be running; attempting to stop old process ($pid) first)"
    kill $pid 2> /dev/null
    rm runwsgiserver.pid
fi

pids=`ps aux | grep runwsgiserver | grep -v "grep" | awk '{print $2}'`
if [ "$pids" ]; then
    echo "(Warning: Web server seems to have been started elsewhere; stopping all processes ($pids))"
    kill $pids
fi

echo "Running the web server on port 8008."
python manage.py runwsgiserver host=0.0.0.0 port=8008 threads=50 daemonize=true pidfile=runwsgiserver.pid
echo "The server should now be accessible locally at: http://127.0.0.1:8008/"
echo "To access it from another connected computer, try the following address(es):"
for ip in `ifconfig | grep 'inet' | grep -P '\d+\.\d+\.\d+\.\d+' | grep -v "127.0.0.1" | cut -d: -f2 | awk '{print $1}'`
do
    echo http://$ip:8008/
done

