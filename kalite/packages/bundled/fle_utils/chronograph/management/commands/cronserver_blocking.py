import time

from django.conf import settings
logging = settings.LOG
from django.core.management.base import BaseCommand
from django.utils.translation import ugettext_lazy as _


shutdown = False


class Command(BaseCommand):
    args = ""
    help = _("Invoked by kalite CLI to run a blocking management command")

    option_list = BaseCommand.option_list + ()

    def handle(self, *args, **options):

        from fle_utils.chronograph.models import Job

        # In case any chronograph threads were interrupted the last time
        # the server was stopped, clear their is_running flags to allow
        # them to be started up again as needed.
        Job.objects.update(is_running=False)
        
        # Apparently, we check for jobs every 10 minutes by default
        sleep_time = getattr(settings, "CRONSERVER_FREQUENCY", 600)
        
        while not shutdown:
            jobs = Job.objects.due()
            
            if jobs:
                logging.info("Running %d due jobs... (%s)" % (jobs.count(), ", ".join(['"%s"' % job.name for job in jobs])))
                for job in jobs:
                    job.run()
            else:
                logging.debug("No jobs due to run.")
            
            # Sleep a little bit at a time to discover if we have to shutdown
            for __ in range(60):
                time.sleep(sleep_time // 60)
                if shutdown:
                    logging.info("Cronserver successfully terminated")
                    break
