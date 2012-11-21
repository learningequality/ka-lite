pids=`ps -C python -f | grep cronserver.py | awk '{print $2}'`

if [ "$pids" ]; then
    echo "(Warning: Cron server may still be running; stopping old process ($pids) first)"
    kill $pids
fi

echo "Starting the cron server in the background."

python cronserver.py &
