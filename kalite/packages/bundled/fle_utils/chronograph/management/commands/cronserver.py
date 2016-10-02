import sys
import warnings
from threading import Thread
from time import sleep
from optparse import make_option
import os
import gc

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext_lazy as _

from ....chronograph.models import Job


class CronThread(Thread):
    daemon = False
    def __init__(self, gc=False, mp=False, *args, **kwargs):
        self.do_gc = gc
        self.do_profile = True

        return super(CronThread, self).__init__(*args, **kwargs)

    def run(self):
        jobs = Job.objects.due()
        
        if self.do_profile:
            try:
                import memory_profiler
                prof_string = "[%8.2f MB] " % memory_profiler.memory_usage()[0]
            except ImportError:
                prof_string = "No profiler found"
        else:
            prof_string = ""

        if jobs:
            logging.info("%sRunning %d due jobs... (%s)" % (prof_string, jobs.count(), ", ".join(['"%s"' % job.name for job in jobs])))
            for job in Job.objects.due():
                job.run()
        else:
            logging.debug("%sNo jobs due to run." % prof_string)

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
        make_option('-d', '--daemon',
            action='store_true',
            dest='daemon',
            default=False,
            help='Spawn to background process (daemonize)'),
        make_option('-i', '--pid-file',
            action='store',
            dest='pidfile',
            default='',
            help='Write PID to file when running as daemon'),
    )
    def handle( self, *args, **options ):
        
        warnings.warn(
            "This command is deprecated. 'kalite start' will create a "
            "thread that runs chronograph."
        )
        
        # Run as daemon, ie. fork the process
        if options['daemon']:
            from django.utils.daemonize import become_daemon
            become_daemon()
            # Running as daemon now. PID is fpid
            pid_file = file(options['pidfile'], "w")
            pid_file.write(str(os.getpid()))
            pid_file.close()

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
            if not options['daemon']:
                sys.stdout.write("Quit the server with CONTROL-C.\n")

            # Run server until killed
            while True:
                thread = CronThread(gc=options.get("gc", False), mp=options.get("prof", False))
                thread.start()
                sleep(time_wait)
        except KeyboardInterrupt:
            logging.info("Exiting...\n")
            sys.exit()