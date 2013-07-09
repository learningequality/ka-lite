from datetime import datetime
from chronograph.models import Job
from croncount import get_count

from settings import LOG as logging
from utils.django_utils import call_command_async


def force_job(command, name="", frequency="YEARLY", stop=False, no_cron=False):
    """
    Mark a job as to run immediately (or to stop).
    By default, call cron directly, to resolve.
    """
    jobs = Job.objects.filter(command=command)
    if jobs.count() > 0:
        job = jobs[0]
    else:
        job = Job(command=command)
        job.frequency = frequency
        job.name = name or command

    if stop:
        job.is_running = False
    else:
        job.next_run = datetime.now()
    job.save()

    if not no_cron:
        # Just start cron directly, so that the process starts immediately.
        # Note that if you're calling force_job frequently, then 
        # you probably want to avoid doing this on every call.
        if get_count() and not job_status(command):
            logging.debug("Ready to launch command '%s'" % command)
            call_command_async("cron")


def job_status(command):
    return Job.objects.filter(command=command, is_running=True).count() > 0
