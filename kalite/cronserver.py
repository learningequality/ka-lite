import threading
import subprocess
import sys
from croncount import get_count

t = None

def cron():
    # only bother spinning up the full cron management command if there's something waiting to be run
    if get_count():
        p = subprocess.Popen(["python", "manage.py", "cron"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = p.communicate()
        if out[0]:
            sys.stdout.write(out[0])
        if out[1]:
            sys.stderr.write("Error: %s\n" % out[1])
            if -1 != out[1].find("no such table: chronograph_job"): # installation failed, don't keep going!
                t.cancel()
    
if __name__ == "__main__":
    t = threading.Timer(5, cron)
    t.start()
