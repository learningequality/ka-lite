"""
Test support harness to make setup.py test work.
"""
import functools
import os
import pdb
import sys
import logging

from django.test.simple import DjangoTestSuiteRunner
from django.core import management

from kalite import settings


def auto_pdb(*exceptions):
    """
    From http://stackoverflow.com/questions/4398967/python-unit-testing-automatically-running-the-debugger-when-a-test-fails
    """
    if not exceptions:
        exceptions = (AssertionError, )
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except:
                pdb.post_mortem(sys.exc_info()[3])
        return wrapper
    return decorator


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
        
        # Purge all .pyc files using the clean_pyc django extension.
        # This prevents issues when py's have been renamed or moved but
        #   the orphan pyc's are discovered and run during testing
        # pyc's are not tracked by git, so orphans can happen when an
        #   older branch has been checked out
        logging.getLogger("kalite").info("Purging pyc files")
        management.call_command('clean_pyc', verbosity=2)
        
        if not test_labels:
            test_labels = {'main', 'central', 'securesync'}
            if settings.CENTRAL_SERVER:
                test_labels -= {'main',}
            else:
                test_labels -= {'central',}
        return super(KALiteTestRunner,self).run_tests(test_labels, extra_tests, **kwargs)

    def build_suite(self, *args, **kwargs):
        """
        Wrap each test function such that it automatically calls PDB on a failure.
        """
        test_suite = super(KALiteTestRunner, self).build_suite(*args, **kwargs)
        for test in test_suite._tests:
            testfun = getattr(test, test._testMethodName)
            setattr(test, test._testMethodName, auto_pdb()(testfun))
        return test_suite