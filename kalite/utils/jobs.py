from datetime import datetime
from chronograph.models import Job

from utils.django_utils import call_command_async


def force_job(command, name="", frequency="YEARLY", stop=False, force_cron=True):
    """
    """
    import pdb; pdb.set_trace()
    force_cron = force_cron and not stop  #cannot stop and force start at the same time.

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

    if force_cron:  # Just start cron directly, so that the process starts immediately.
        call_command_async("cron")


def job_status(command):
    return Job.objects.filter(command=command, is_running=True).count() > 0
