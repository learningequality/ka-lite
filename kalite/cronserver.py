import os
import subprocess
import sys
import threading
from croncount import get_count

import settings  # get cron settings from Django project settings file


def cron():
    # only bother spinning up the full cron management command if there's something waiting to be run
    if get_count():
        # Use sys to get the same executable running as is running this process.
        # Make sure to call the manage.py from this project.
        subprocess.call([sys.executable, os.path.join(settings.PROJECT_PATH, "manage.py"), "cron"])

    # This is the pause between executions.  If the above hangs for a long time,
    #   we won't check again until it has returned / completed.
    threading.Timer(settings.CRONSERVER_FREQUENCY, cron).start()


if __name__ == "__main__":
    cron()