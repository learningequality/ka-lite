from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.utils.translation import ugettext_lazy as _

from chronograph.models import Job

import logging
import sys

from datetime import datetime
from time import sleep, time
from threading import Thread

logger = logging.getLogger('chronograph.commands.cronserver')

class CronThread(Thread):
    daemon = True
    
    def run(self):
        logger.info("Running due jobs...")
        call_command('cron')

class Command(BaseCommand):
    args = "time"
    help = _("Emulates a reoccurring cron call to run jobs at a specified "
             "interval.  This is meant primarily for development use.")
    
    
    def handle( self, *args, **options ):
        from django.core.management import call_command
        
        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            datefmt="%Y-%m-%d %H:%M:%S",
                            format="[%(asctime)-15s] %(message)s")
        
        try:
            time_wait = int(args[0])
        except:
            time_wait = 60
        
        try:
            sys.stdout.write("Starting cronserver.  Jobs will run every %d seconds.\n" % time_wait)
            sys.stdout.write("Quit the server with CONTROL-C.\n")
            
            seconds = datetime.now().second
            if seconds > 0:
                sleep(60-seconds)
            
            # Run server untill killed
            while True:
                thread = CronThread()
                thread.start()
                sleep(time_wait)
        except KeyboardInterrupt:
            logger.info("Exiting...\n")
            sys.exit()