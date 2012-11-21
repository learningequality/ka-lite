pids=`ps -C python -f | grep cronserver.py | awk '{print $2}'`

if [ "$pids" ]; then
    echo "----------------------------------------------------------------"
    echo "Killing all existing cron server processes ($pids)."
    echo "----------------------------------------------------------------"
    kill $pids
else
    echo "----------------------------------------------------------------"
    echo "Cron server does not seem to be running."
    echo "----------------------------------------------------------------"
fi
