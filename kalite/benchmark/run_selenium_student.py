
"""
Very temporary test harness

python ./kalite/benchmark/run_selenium_student.py &

"""

#!/usr/bin/env python2

import os
import sys
import random
import datetime
import time

# Set up the paths
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [script_dir + "/../../../ka-lite/kalite/../python-packages/"] + sys.path
sys.path = [script_dir + "/../../../ka-lite/kalite/../"] + sys.path
sys.path = [script_dir + "/../../../ka-lite/kalite"] + sys.path

#import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'kalite.settings'

import benchmark_test_cases
import settings

print "-----------------------"
print "SeleniumStudent sequence"
print "-----------------------"
try:
    profile=sys.argv[1]
except:
    profile=0
    
print "profile:", profile


for x in range(1):
    now = datetime.datetime.today()
    #while (now.minute / 5.) != (now.minute /5):
    #    time.sleep(20)
    #    now = datetime.datetime.today()
            
    bench = benchmark_test_cases.SeleniumStudentExercisesOnly(comment="with nginx"
                                                , username="stevewall"
                                                , password="student"
                                                , url="http://192.168.1.25:8008"
                                                , starttime="00:00"
                                                , duration=2
                                                , behaviour_profile=profile)
    print bench.execute()
