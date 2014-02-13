from datetime import datetime
from chronograph.models import Job

from django.db.models.signals import post_save
from django.dispatch import receiver

import settings
from settings import LOG as logging
from updates.models import UpdateProgressLog
from utils.django_utils import call_command_async


def force_job(command, name="", frequency="YEARLY", stop=False, launch_cron=True):
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
        launch_cron = False
    else:
        job.next_run = datetime.now()
    job.save()

    if launch_cron and not job.is_running:  # don't run the same job twice
        # Just start cron directly, so that the process starts immediately.
        # Note that if you're calling force_job frequently, then
        # you probably want to avoid doing this on every call.
        if get_ready_count() > 0:
            logging.debug("Ready to launch command '%s'" % command)
            call_command_async("cron")

@receiver(post_save, sender=Job)
def my_handler(sender, **kwargs):
    job = kwargs['instance']
    if not job.is_running:
        # Update progress log to be cancelled as well.
        UpdateProgressLog.objects \
            .filter(process_name=job.command, completed=False) \
            .update(completed=True)

def get_ready_count():
    return Job.objects.filter(disabled=False, is_running=False, next_run__lte=datetime.now()).count()

def job_status(command):
    return Job.objects.filter(command=command, is_running=True).count() > 0