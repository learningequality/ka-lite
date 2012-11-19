from datetime import datetime
from chronograph.models import Job

def force_job(command, name):
    jobs = Job.objects.filter(command=command)
    if jobs.count() > 0:
        job = jobs[0]
    else:
        job = Job(command=command)
        job.frequency = "YEARLY"
        job.name = name
        job.next_run = datetime.now()
    job.force_run = True
    job.save()