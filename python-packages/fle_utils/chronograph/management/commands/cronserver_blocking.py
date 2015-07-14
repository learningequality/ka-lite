import time

from django.conf import settings
logging = settings.LOG
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _


shutdown = False


class Command(BaseCommand):
    args = ""
    help = _("Used by kalitectl.py to run a blocking management command")

    option_list = BaseCommand.option_list + ()

    def handle(self, *args, **options):

        from fle_utils.chronograph.models import Job

        # In case any chronograph threads were interrupted the last time
        # the server was stopped, clear their is_running flags to allow
        # them to be started up again as needed.
        Job.objects.update(is_running=False)
        
        sleep_time = getattr(settings, "CRONSERVER_FREQUENCY", 60)
        
        while not shutdown:
            jobs = Job.objects.due()
            
            if jobs:
                logging.info("Running %d due jobs... (%s)" % (jobs.count(), ", ".join(['"%s"' % job.name for job in jobs])))
                for job in jobs:
                    job.run()
            else:
                logging.debug("No jobs due to run.")
            
            # Sleep a little bit at a time to discover if we have to shutdown
            for __ in range(6):
                time.sleep(sleep_time // 6)
                if shutdown:
                    break
