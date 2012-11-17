import datetime
import time

from django.core.management import _commands, call_command
from django.test import TestCase

from chronograph.models import Job, Log, freqs
from chronograph.tests.commands import Sleeper

try:
    from django.utils import unittest
except:
    import unittest



class JobTestCase(TestCase):
    fixtures = ['test_jobs.json']
    
    def setUp(self):
        # Install the test command; this little trick installs the command
        # so that we can refer to it by name
        _commands['test_sleeper'] = Sleeper()
    
    def testJobRun(self):
        """
        Test that the jobs run properly.
        """
        for job in Job.objects.due():
            time_expected = float(job.args)
            
            time_start = time.time()
            job.run()
            time_end = time.time()
            
            time_taken = time_end - time_start
            self.assertAlmostEqual(time_taken, time_expected, delta=1.2)
    
    def testCronCommand(self):
        """
        Test that the ``cron`` command runs all jobs in parallel.
        """
        
        # Pick the longest running Job
        job = sorted(Job.objects.due().filter(command="test_sleeper"), key=lambda j: -int(j.args))[0]
        
        # The "args" property simply describes the number of seconds the Job
        # should take to run
        time_expected = float(job.args)
        
        time_start = time.time()
        call_command('cron')
        time_end = time.time()
        
        time_taken = time_end - time_start
        self.assertAlmostEqual(time_taken, time_expected, delta=1.2)
    
    def testCronCleanCommand(self):
        """
        Test that the ``cron_clean`` command runs properly.
        """
        # Pick the shortest running Job
        job = sorted(Job.objects.due().filter(command="test_sleeper"), key=lambda j: int(j.args))[0]
        
        # Run the job 5 times
        for i in range(5):
            job.run()
        
        # Ensure that we have 5 Log objects
        self.assertEqual(Log.objects.count(), 5)
        
        # Now clean out the logs that are older than 0 minutes (all of them)
        call_command('cron_clean', 'minutes', '0')
        
        # Ensure that we have 0 Log objects
        self.assertEqual(Log.objects.count(), 0)
