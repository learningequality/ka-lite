#!/bin/bash
# Author: Louis Steele, July 2014
#
# This script makes backups of the data.sqlite file
# and deletes backups that are over 2 weeks old.
# Uses the following format to organize the files:
# week-day-data.sqlite

#Week of the year (1-53)
WEEK=$(date +"%V")
#Day of the week (1-7, 1 is Monday)
DAY=$(date +"%u")

#Directory of this script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

#Make a copy of data.sqlite for today
cp -v $DIR/kalite/database/data.sqlite $DIR/ka-lite-data-backup/$WEEK-$DAY-data.sqlite

#Now to delete backups more than 2 weeks old (with some funky business due to the ISO week number):
if [ "$WEEK" = 1 ]; then
 rm -v $DIR/ka-lite-data-backup/51* 
elif [ "$WEEK" = 2 ]; then
 rm -v $DIR/ka-lite-data-backup/52* $DIR/ka-lite-data-backup/53*
else
 rm -v $DIR/ka-lite-data-backup/$(($WEEK-2))*
fi
