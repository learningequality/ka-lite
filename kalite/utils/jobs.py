from datetime import datetime
from chronograph.models import Job

def force_job(command, name="", frequency="YEARLY", stop=False):
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