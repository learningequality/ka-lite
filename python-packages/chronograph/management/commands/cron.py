from django.core.management.base import BaseCommand

import logging
import os
import sys
import time

from multiprocessing import Process

logger = logging.getLogger('chronograph.commands.cron')

class JobProcess(Process):
    """
    Each ``Job`` gets run in it's own ``Process``.
    """
    daemon = True
    
    def __init__(self, job, *args, **kwargs):
        self.job = job
        Process.__init__(self, *args, **kwargs)
    
    def run(self):
        logger.info("Running Job: '%s'" % self.job)
        self.job.run()

class Command(BaseCommand):
    help = 'Runs all jobs that are due.'
    
    def handle(self, *args, **options):
        from chronograph.models import Job
        
        procs = []
        for job in Job.objects.due():
            if not job.check_is_running():
                # Only run the Job if it isn't already running
                proc = JobProcess(job)
                proc.start()
                procs.append(proc)
        
        logger.info("%d Jobs are due" % len(procs))
        
        # Keep looping until all jobs are done
        while procs:
            for i in range(len(procs)):
                if not procs[i].is_alive():
                    procs.pop(i)
                    break
                time.sleep(.1)
                