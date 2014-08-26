"""
These use a web-browser, along selenium, to simulate user actions.
"""
import random
import string

from django.conf import settings
from django.utils import unittest

from .base import KALiteDistributedWithFacilityBrowserTestCase
from kalite.facility.models import FacilityUser
from kalite.main.models import UserLog
from kalite.testing.utils import FuzzyInt
from kalite.testing.mixins.securesync_mixins import CreateDeviceMixin

@unittest.skipIf(getattr(settings, 'HEADLESS', None), "Doesn't work on HEADLESS.")
class QueryTest(CreateDeviceMixin, KALiteDistributedWithFacilityBrowserTestCase):
    """"""
    def __init__(self, *args, **kwargs):
        """To guarantee state across tests, clear browser state every time."""
        random.seed('ben')  # to make password reproducible
        self.persistent_browser = False
        super(QueryTest, self).__init__(*args, **kwargs)

    def setUp(self):
        self.setup_fake_device()
        super(QueryTest, self).setUp()

    @staticmethod
    def _gen_valid_password():
        return ''.join(random.sample(string.ascii_lowercase, settings.PASSWORD_CONSTRAINTS['min_length']))

    def test_query_login_admin(self):
        with self.assertNumQueries(FuzzyInt(35, 41)):
            self.browser_login_admin()

    def test_query_login_teacher(self):
        """Check the # of queries when logging in as a teacher."""
        teacher = FacilityUser(is_teacher=True, username="t1", facility=self.facility)
        passwd = self._gen_valid_password()
        teacher.set_password(passwd)
        teacher.save()

        with self.assertNumQueries(FuzzyInt(25, 34) + 3 * UserLog.is_enabled()):
            self.browser_login_teacher("t1", passwd, self.facility)

    def test_query_login_student(self):
        """Check the # of queries when logging in as a student."""
        student = FacilityUser(is_teacher=False, username="s1", facility=self.facility)
        passwd = self._gen_valid_password()
        student.set_password(passwd)
        student.save()

        expected_num_queries = 29 + 3*UserLog.is_enabled()
        with self.assertNumQueries(FuzzyInt(expected_num_queries - 3, expected_num_queries + 5)):
            self.browser_login_student("s1", passwd, self.facility)

    def test_query_status_admin(self):
        """"""
        self.test_query_login_admin()
        with self.assertNumQueries(FuzzyInt(3, 9)):
            self.browse_to(self.reverse("status"))

    def test_query_status_teacher(self):
        """"""
        self.test_query_login_teacher()
        with self.assertNumQueries(FuzzyInt(2, 6)):
            self.browse_to(self.reverse("status"))

    def test_query_status_student(self):
        """"""
        self.test_query_login_student()
        with self.assertNumQueries(FuzzyInt(0, 7)):
            self.browse_to(self.reverse("status"))

    def test_query_logout_admin(self):
        """"""
        self.test_query_login_admin()
        with self.assertNumQueries(FuzzyInt(6, 7) + 0*UserLog.is_enabled()):
            self.browser_logout_user()

    def test_query_logout_teacher(self):
        """"""
        self.test_query_login_teacher()
        with self.assertNumQueries(FuzzyInt(5, 11) + 11*UserLog.is_enabled()):
            self.browser_logout_user()

    def test_query_logout_student(self):
        """"""
        self.test_query_login_student()
        with self.assertNumQueries(FuzzyInt(4, 11) + 11*UserLog.is_enabled()):
            self.browser_logout_user()

    def test_query_goto_math_logged_out(self):
        """Check the # of queries when browsing to the "Math" topic page"""

        # Without login
        with self.assertNumQueries(4):
            self.browse_to(self.live_server_url + "/math/")

    def test_query_goto_math_logged_in(self):
        """Check the # of queries when browsing to the "Math" topic page"""

        self.test_query_login_student()
        with self.assertNumQueries(FuzzyInt(0, 7)):
            self.browse_to(self.live_server_url + "/math/")
