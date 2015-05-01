import cProfile
import os
import sys

from time import strftime

sys.path.insert(0, ".")
from kalitectl import start

try:
    filename = sys.argv[1]
except:
    filename = "server_start_profile.dat"
pr = cProfile.Profile()
try:
    # Start profiling...
    pr.enable()
    start(debug=True, args=["--traceback"], skip_job_scheduler=True)
finally:
    # When you get tired or accidentally hit CTRL-C, the profiler will wrap up
    pr.disable()
    fn, ext = os.path.splitext(filename)
    pr.dump_stats(fn + strftime("%Y-%m-%d-%H-%M-%S") + ext)