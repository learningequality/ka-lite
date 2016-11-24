from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError

import shutil
import tempfile
import os
import csv
import glob
from datetime import timedelta
import datetime
from django.db.models import Sum

from kalite.main.models import *
from kalite.facility.models import *
from kalite.topic_tools.content_models import get_topic_contents


class Command(BaseCommand):
    # args = "<data_type=[facility,facility_users,facility_groups,default=exercises,videos]>"

    # help = "Generate fake user data.  Can be re-run to generate extra exercise and video data."

    option_list = BaseCommand.option_list + (
        make_option('-d', '--directory',
            action='store',
            dest='directory',
            default="~/Downloads/databases",
            help='Source directory to look for databases in.'),
        make_option('-t', '--days',
            action='store',
            dest='days',
            default="8",
            help='Number of days to include in time filter.'),
    )

    def handle(self, *args, **options):

        directory = os.path.expanduser(options["directory"])

        temp_db_location = tempfile.mkstemp(suffix=".sqlite")[1]

        settings.DATABASES["default"]["NAME"] = temp_db_location

        csv_header = ["facility", "total_number_of_accounts", "number_of_active_accounts", "number_students_seen_video", "number_students_answered_exercise"]
        full_csv_data = [csv_header]

        time_window_in_days = int(options["days"])

        cutoff_time = datetime.now()-timedelta(days=time_window_in_days)

        for database in glob.glob(os.path.join(directory, "*.sqlite")):

            shutil.copy(database, temp_db_location)

            total_number_of_accounts = FacilityUser.objects.count()
            recent_attempt_logs = AttemptLog.objects.filter(timestamp__gt=cutoff_time).values_list("user_id", flat=True).distinct()
            recent_video_logs = VideoLog.objects.filter(latest_activity_timestamp__gt=cutoff_time).values_list("user_id", flat=True).distinct()

            facilityname = os.path.splitext(database.split("/")[-1])[0]

            csv_row = [facilityname, total_number_of_accounts, len(set(list(recent_attempt_logs) + list(recent_video_logs))), len(recent_video_logs), len(recent_attempt_logs)]
            full_csv_data.append(csv_row)

            print csv_row

        with open(os.path.join(directory, "activity_%d.csv" % time_window_in_days), "w") as f:
            writer = csv.writer(f)
            writer.writerows(full_csv_data)

