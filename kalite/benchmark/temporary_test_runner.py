
"""
Very temporary test harness

python ./kalite/benchmark/temporary_test_runner.py

"""

#!/usr/bin/env python2

import os
import sys
import random

# Set up the paths
script_dir = os.path.dirname(os.path.realpath(__file__))
sys.path = [script_dir + "/../../../ka-lite/kalite/../python-packages/"] + sys.path
sys.path = [script_dir + "/../../../ka-lite/kalite/../"] + sys.path
sys.path = [script_dir + "/../../../ka-lite/kalite"] + sys.path



#import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'kalite.settings'

import benchmark_test_cases
import settings


class Run_me(object):
    def __init__(self):


        print "=========================="
        print "temporary benchmark runner"
        print "=========================="

        print "-------------------------------"
        print "Hello world test (2 iterations)"
        print "-------------------------------"

        bench = benchmark_test_cases.HelloWorld(comment="Random sleeps")
        result_dict = bench.execute(iterations=2)
        print result_dict
        print "Average elapsed (sec):", str(result_dict['average_elapsed'])

        print "------------------------------------"
        print "Validate models test (10 iterations)"
        print "------------------------------------"

        bench = benchmark_test_cases.ValidateModels(comment="Validation x 10")
        result_dict = bench.execute(iterations=10)

        print "Average elapsed (sec):", str(result_dict['average_elapsed'])

        print "dictionary returned is:"
        print result_dict


class Generate_data_in_live(object):
    def __init__(self):
        # IMPORTANT THE ONE BELOW WILL PERMANENTLY ADD STUDENTS and FACILITIES TO YOUR DB !!!!
        print "-----------------------"
        print "Generate facility users"
        print "-----------------------"

        bench = benchmark_test_cases.Generate_facility_users(comment="Test some real database access")
        result_dict = bench.execute()
        print "Elapsed (sec):", str(result_dict['average_elapsed'])


class LoginLogout(object):
    def __init__(self):
        print "-----------------------"
        print "Login logout sequence"
        print "-----------------------"
        bench = benchmark_test_cases.LoginLogout(comment="test some real database access"
                                                , url="http://192.168.1.24:8008"
                                                , username="stevewall"
                                                , password="student")
        print bench.execute(iterations=10)

class SeleniumStudent(object):
    def __init__(self):
        print "-----------------------"
        print "SeleniumStudent sequence"
        print "-----------------------"
        bench = benchmark_test_cases.SeleniumStudent(comment="Test some real database access"
                                                , username="stevewall"
                                                , password="student"
                                                , url="http://192.168.1.24:8008"
                                                , starttime="12:02"
                                                , duration=15
                                                ,behaviour_profile=(random.random()*200))
        print bench.execute()
SeleniumStudent()