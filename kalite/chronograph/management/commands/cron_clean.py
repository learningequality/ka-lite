from django.core.management.base import BaseCommand

class Command( BaseCommand ):
    help = 'Deletes old job logs.'
    
    def handle( self, *args, **options ):
        from chronograph.models import Log
        from datetime import datetime, timedelta
        if len( args ) != 2:
            print 'Command requires two argument. Unit (weeks, days, hours or minutes) and interval.'
            return
        else:
            unit = str( args[ 0 ] )
            if unit not in [ 'weeks', 'days', 'hours', 'minutes' ]:
                print 'Valid units are weeks, days, hours or minutes.'
                return
            try:
                amount = int( args[ 1 ] ) 
            except ValueError:
                print 'Interval must be an integer.'
                return
        kwargs = { unit: amount }
        time_ago = datetime.now() - timedelta( **kwargs )
        Log.objects.filter( run_date__lte = time_ago ).delete()