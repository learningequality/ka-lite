from datetime import datetime

from .models import Job
from fle_utils.django_utils.command import call_command_async


def force_job(command, name="", frequency="YEARLY", stop=False, **kwargs):
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

    job.name = job.name or name or command

    job.save()

    if stop:
        job.is_running = False
    else:
        job.next_run = datetime.now()
        job.args = " ".join(["%s=%s" % (k, v) for k, v in kwargs.iteritems()])

    job.save()

    # Set as variable so that we could pass as param later, if we want to!
    launch_job = not stop and not job.is_running
    if launch_job:  # don't run the same job twice
        # Just start cron directly, so that the process starts immediately.
        # Note that if you're calling force_job frequently, then
        # you probably want to avoid doing this on every call.
        if Job.objects.filter(disabled=False, is_running=False, next_run__lte=datetime.now()).count() > 0:
            # logging.debug("Ready to launch command '%s'" % command)
            call_command_async("cron")
