cd `dirname "${BASH_SOURCE[0]}"`/kalite
if [ -f "database/data.sqlite" ]; then
	echo
	./cronstart.sh
	echo
	./serverstart.sh
else
	echo "Run install.sh first!"
fi