#!/usr/bin/env python
import os, sys
from datetime import datetime

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path = [PROJECT_PATH, os.path.join(PROJECT_PATH, "../"), os.path.join(PROJECT_PATH, "../python-packages/")] + sys.path

import settings

def get_count():

    try:

        import sqlite3

        conn = sqlite3.connect(settings.DATABASES["default"]["NAME"])

        cursor = conn.cursor()

        cursor.execute("""SELECT COUNT(*) FROM "chronograph_job"
                     WHERE ("chronograph_job"."disabled" = 0
                     AND "chronograph_job"."is_running" = 0
                     AND "chronograph_job"."next_run" <= ?)""", (str(datetime.now()),))

        count = cursor.fetchone()[0]
        
        return count

    except:
        
        return "Error checking due job count. Assume the worst."
        
if __name__ == "__main__":
    count = get_count()
    if isinstance(count, int):
        if count:
            print "There are currently %d jobs waiting to be run." % count
        else:
            print "There are no jobs waiting to be run."
    else:
        print count
