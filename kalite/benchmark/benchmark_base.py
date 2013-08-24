""" base class for KA-LITE benchmarks

    Provides a wrapper for benchmarks, specifically to:
    a) accurately record the test conditions/environment
    b) to record the duration of the task
    d) to allow multiple iterations of the task so that
        an average time can be calculated
        
    Benchmark results are returned in a python dict

    These benchmarks do not use unittest or testrunner frameworks
"""
import time
import random
import platform
import subprocess
    
class Common(object):

    def __init__(self, comment=None, fixture=None, **kwargs):

        self.return_dict = {}
        self.return_dict['comment'] = comment
        self.return_dict['class']=type(self).__name__
        self.return_dict['uname'] = platform.uname()
        self.return_dict['fixture'] = fixture
                                
        try:
            branch = subprocess.Popen(["git", "describe", "--contains", "--all", "HEAD"], stdout=subprocess.PIPE).communicate()[0]
            self.return_dict['branch'] = branch[:-1]
            head = subprocess.Popen(["git", "log", "--pretty=oneline", "--abbrev-commit", "--max-count=1"], stdout=subprocess.PIPE).communicate()[0]
            self.return_dict['head'] = head[:-1]
        except:
            self.return_dict['branch'] = None
            self.return_dict['head'] = None            

        self._setup(**kwargs)

    def execute(self, iterations=1):

        if iterations < 1: iterations = 1

        if hasattr(self, 'max_iterations'):
            if iterations > self.max_iterations:
                iterations = self.max_iterations
        
        self.return_dict['iterations'] = iterations
        self.return_dict['individual_elapsed'] = {}
        self.return_dict['post_execute_info'] = {}
        for i in range(iterations):
            start_time = time.time()
            self._execute()
            self.return_dict['individual_elapsed'][i+1] = time.time() - start_time
            self.return_dict['post_execute_info'][i+1] = self._get_post_execute_info()
        
        sum = 0.0
        for i in self.return_dict['individual_elapsed']:
            sum += self.return_dict['individual_elapsed'][i]
        self.return_dict['average_elapsed'] = sum / len(self.return_dict['individual_elapsed'])
         
        self._teardown()

        return self.return_dict

    def _setup(self, **kwargs): pass
    def _execute(self): pass
    def _teardown(self): pass
    def _get_post_execute_info(self): pass    
