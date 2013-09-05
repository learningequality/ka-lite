#!/bin/bash

#!/bin/bash

current_dir=`dirname "${BASH_SOURCE[0]}"`
if [ -e "$current_dir/serverstart.sh" ]; then
    KALITE_DIR=$current_dir/../kalite
else
    SCRIPT_DIR=$current_dir/scripts
    KALITE_DIR=$current_dir/kalite
fi

if [ -e "$KALITE_DIR/database/data.sqlite" ] ; then
	
    # move any previously downloaded content from the old location to the new
	mv "$KALITE_DIR/static/videos/*" "$KALITE_DIR/../content" > /dev/null 2> /dev/null

	echo
	source "$current_dir/cronstart.sh"
	echo
	source "$current_dir/serverstart.sh"
else
	echo "Please run install.sh first!"
fi

cd ..
