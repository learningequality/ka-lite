# run the development server inside docker
ID=$(docker run -d -p 8000 ka-lite-installed /bin/sh -c "/start-ka-lite.sh");
echo "Docker ID=$ID"

# sleep, to give the server some time to start up
sleep 20

# get the port, so we can do stuff with it
PORT=$(docker port $ID 8000)
echo "Docker port=$PORT"

# such as check that the server is running
curl --head http://localhost:$PORT/

# sleep, to give time to access the url remotely
echo "Sleeping for 30 secs; try accessing at http://playground.learningequality.org:$PORT/"
sleep 30

# and then we can kill the instance, when done!
docker kill $ID
