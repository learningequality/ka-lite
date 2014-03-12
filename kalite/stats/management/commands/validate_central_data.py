import sys
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Max, Sum, Avg, Q, F

import settings
from main.models import *
from securesync.models import *
from settings import LOG as logging

class Command(BaseCommand):
    help = "Create a zip file with all code, that can be unpacked anywhere."

    option_list = BaseCommand.option_list
    """
        make_option('-f', '--file',
            action='store',
            dest='zip_file',
            default=None,
            help='FILE to unzip from',
            metavar="FILE"),
        make_option('-p', '--port',
            action='store',
            dest='test_port',
            default=9157,  # 'Random' test port.  Hopefully open!
            help='PORT where we can test KA Lite',
            metavar="PORT"),
        make_option('-i', '--interactive',
            action="store_true",
            dest="interactive",
            default=False,
            help="Display interactive prompts"),
        )
    """

    def handle(self, *args, **options):

        # Lambda functions for display and dump to json
        p = lambda rows: ([sys.stdout.write("%s\n" % row) or "" for row in rows])
        dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
        d = lambda qset, file: open(file, "w").write(json.dumps(qset, default=dthandler))


        #### Validation ####

        sys.stderr.write("\nVideo logs that are complete, but points < 750\n")
        vo = VideoLog.objects \
            .filter(Q(points__lt=750) | Q(points__gt=750), complete=True) \
            .values("points", "completion_timestamp") \
            .order_by("completion_timestamp")
        "".join(p(vo))

        sys.stderr.write("\nExercise logs that are complete, but attempts < 10\n")
        #
        # Indicates failures to save attempts
        eo = ExerciseLog.objects \
            .filter(attempts__lt=10, complete=True) \
            .values("attempts", "attempts_before_completion", "points", "completion_timestamp") \
            .order_by("completion_timestamp")
        "".join(p(eo))

