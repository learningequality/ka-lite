import threading, subprocess
from croncount import get_count

def cron():
    # only bother spinning up the full cron management command if there's something waiting to be run
    if get_count():
        subprocess.call(["python", "manage.py", "cron"])
    threading.Timer(5, cron).start()

if __name__ == "__main__":
    cron()