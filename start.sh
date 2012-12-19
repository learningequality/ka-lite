cd `dirname "${BASH_SOURCE[0]}"`/kalite

# move any previously downloaded content from the old location to the new
mv static/videos/* ../content

echo
./cronstart.sh
echo
./serverstart.sh
