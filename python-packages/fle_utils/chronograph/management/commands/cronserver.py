import sys
import warnings
from datetime import datetime
from threading import Thread
from time import sleep, time
from optparse import make_option
try:
    import memory_profiler
except Exception as e:
    pass
import gc

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils.translation import ugettext_lazy as _

from ....chronograph.models import Job
from kalite.settings import LOG as logger


class CronThread(Thread):
    daemon = True
    def __init__(self, gc=False, mp=False, *args, **kwargs):
        self.do_gc = gc

        if mp and not "memory_profiler" in sys.modules.keys():
            mp = False
            warnings.warn("memory_profiling disabled.")
        self.do_profile = mp


        return super(CronThread, self).__init__(*args, **kwargs)

    def run(self):
        jobs = Job.objects.due()
        prof_string = "" if not self.do_profile else "[%8.2f MB] " % memory_profiler.memory_usage()[0]

        if jobs:
            logger.info("%sRunning %d due jobs... (%s)" % (prof_string, jobs.count(), ", ".join(['"%s"' % job.name for job in jobs])))
            call_command('cron')
        else:
            logger.debug("%sNo jobs due to run." % prof_string)

        if self.do_gc:
            gc.collect()

class Command(BaseCommand):
    args = "time"
    help = _("Emulates a reoccurring cron call to run jobs at a specified "
             "interval.  This is meant primarily for development use.")

    option_list = BaseCommand.option_list + (
        make_option('-g', '--nogc',
            action='store_false',
            dest='gc',
            default=True,  # known memory leak, so keep True by default
            help='Block garbage collection after every execution'),
        make_option('-p', '--prof',
            action='store_true',
            dest='prof',
            default=False,
            help='Print memory profiling information'),
    )
    def handle( self, *args, **options ):

        #logging.basicConfig(stream=sys.stdout,
        #                    datefmt="%Y-%m-%d %H:%M:%S",
        #                    format="[%(asctime)-15s] %(message)s")

        try:
            # Specify polling frequency either on the command-line or inside settings
            if args and args[0].strip():
                time_wait = float(args[0])
            else:
                time_wait = getattr(settings, "CRONSERVER_FREQUENCY", 60)
        except:
            raise CommandError("Invalid wait time: %s is not a number." % args[0])

        try:
            sys.stdout.write("Starting cronserver.  Jobs will run every %d seconds.\n" % time_wait)
            #sys.stdout.write("Quit the server with CONTROL-C.\n")

            # Run server until killed
            while True:
                thread = CronThread(gc=options.get("gc", False), mp=options.get("prof", False))
                thread.start()
                sleep(time_wait)
        except KeyboardInterrupt:
            logger.info("Exiting...\n")
            sys.exit()