"""
Test support harness to make setup.py test work.
"""

import os
import sys

from django.test.simple import DjangoTestSuiteRunner

from kalite import settings

class KALiteTestRunner(DjangoTestSuiteRunner):
    """Forces us to start in liveserver mode, and only includes relevant apps to test"""
    
    def __init__(self, *args, **kwargs):
        """Force setting up live server test.  Adding to kwargs doesn't work, need to go to env.
        Dependent on how Django works here."""
        
        # If no liveserver specified, set some default.
        #   port range is the set of open ports that Django can use to 
        #   start the server.  They may have multiple servers open at once.
        if not os.environ.get('DJANGO_LIVE_TEST_SERVER_ADDRESS',""):
            os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "localhost:9000-9999"
        return super(KALiteTestRunner, self).__init__(*args, **kwargs)
        
    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        """By default, only run relevant app tests.  If you specify... you're on your own!"""
        if not test_labels:
            test_labels = {'main', 'central', 'securesync'}
            if settings.CENTRAL_SERVER:
                test_labels -= {'main',}
            else:
                test_labels -= {'central',}
        return super(KALiteTestRunner,self).run_tests(test_labels, extra_tests, **kwargs)
        