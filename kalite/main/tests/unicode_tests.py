import sys
from datetime import datetime  # main.models imports this way, so we have this hacky dependency.

from django.utils import unittest

import settings
import version
from facility.models import Facility, FacilityGroup, FacilityUser
from main.models import *
from main.tests.base import MainTestCase
from securesync.models import Device
from testing import UnicodeModelsTest

class MainUnicodeModelsTest(MainTestCase, UnicodeModelsTest):

    @unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
    def test_unicode_class_coverage(self):
        # Make sure we're testing all classes
        self.check_unicode_class_coverage(
            models_module="main.models",
            known_classes = [ExerciseLog, UserLog, UserLogSummary, VideoLog],
        )


    def test_unicode_string(self):
        # Dependencies
        dev = Device.get_own_device()
        self.assertNotIn(unicode(dev), "Bad Unicode data", "Device: Bad conversion to unicode.")

        fac = Facility(name=self.korean_string)
        fac.save()
        self.assertNotIn(unicode(fac), "Bad Unicode data", "Facility: Bad conversion to unicode.")

        fg = FacilityGroup(facility=fac, name=self.korean_string)
        fg.save()
        self.assertNotIn(unicode(fg), "Bad Unicode data", "FacilityGroup: Bad conversion to unicode.")

        user = FacilityUser(
            facility=fac,
            group=fg,
            first_name=self.korean_string,
            last_name=self.korean_string,
            username=self.korean_string,
            notes=self.korean_string,
        )
        user.set_password(self.korean_string * settings.PASSWORD_CONSTRAINTS["min_length"])
        user.save()
        self.assertNotIn(unicode(user), "Bad Unicode data", "FacilityUser: Bad conversion to unicode.")

        known_classes = [ExerciseLog, UserLog, UserLogSummary, VideoLog]

        #
        elog = ExerciseLog(user=user, exercise_id=self.korean_string)
        self.assertNotIn(unicode(elog), "Bad Unicode data", "ExerciseLog: Bad conversion to unicode (before saving).")
        elog.save()
        self.assertNotIn(unicode(elog), "Bad Unicode data", "ExerciseLog: Bad conversion to unicode (after saving).")

        vlog = VideoLog(user=user, video_id=self.korean_string, youtube_id=self.korean_string)
        self.assertNotIn(unicode(vlog), "Bad Unicode data", "VideoLog: Bad conversion to unicode (before saving).")
        vlog.save()
        self.assertNotIn(unicode(vlog), "Bad Unicode data", "VideoLog: Bad conversion to unicode (after saving).")

        ulog = UserLog(user=user)
        self.assertNotIn(unicode(ulog), "Bad Unicode data", "UserLog: Bad conversion to unicode.")

        ulogsum = UserLogSummary(
            user=user,
            device=dev,
            activity_type=1,
            start_datetime=datetime.now(),
            end_datetime=datetime.now(),
        )
        self.assertNotIn(unicode(ulogsum), "Bad Unicode data", "UserLogSummary: Bad conversion to unicode.")
