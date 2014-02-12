from chronograph.models import Job

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import UpdateProgressLog
from .videos import *


@receiver(post_save, sender=Job)
def my_handler(sender, **kwargs):
    job = kwargs['instance']
    if not job.is_running:
        # Update progress log to be cancelled as well.
        UpdateProgressLog.objects \
            .filter(process_name=job.command, completed=False) \
            .update(completed=True)
