import cProfile
import os
import sys

from time import strftime

sys.path.insert(0, ".")
from kalitectl import manage

try:
    filename = sys.argv[1]
except:
    filename = "server_start_profile.dat"
pr = cProfile.Profile()
try:
    # Start profiling...
    pr.enable()
    manage("runserver", args=["--traceback"])
finally:
    # When you get tired or accidentally hit CTRL-C, the profiler will wrap up
    pr.disable()
    fn, ext = os.path.splitext(filename)
    stamped_filename = fn + strftime("%Y-%m-%d-%H-%M-%S") + ext
    print "Dumping to %s" % stamped_filename
    pr.dump_stats(stamped_filename)