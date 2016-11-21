from django.core.management.base import BaseCommand

from ...models import Job


class Command(BaseCommand):
    help = 'Runs all jobs that are due.'

    def handle(self, *args, **options):
        for job in Job.objects.due():
            job.run()
