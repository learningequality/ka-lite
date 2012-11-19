import time

from django.core.management.base import BaseCommand, CommandError

class Sleeper(BaseCommand):
    args = '[time in seconds to loop]'
    help = 'A simple command that simply sleeps for the specified duration'
    
    def handle(self, *args, **options):
        start_time = time.time()
        
        try:
            target_time = float(args[0])
        except:
            target_time = 10
        time.sleep(target_time)
        
        end_time = time.time()
        print "Job ran for %f seconds" % (end_time-start_time)