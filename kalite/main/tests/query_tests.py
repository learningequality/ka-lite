"""
These use a web-browser, along selenium, to simulate user actions.
"""
from django.utils import unittest

import settings
from .browser_tests import KALiteDistributedWithFacilityBrowserTestCase
from main.models import UserLog
from securesync.models import FacilityUser
from shared.testing.decorators import distributed_server_test


@distributed_server_test
class QueryTest(KALiteDistributedWithFacilityBrowserTestCase):
    """"""
    def __init__(self, *args, **kwargs):
        """To guarantee state across tests, clear browser state every time."""
        self.persistent_browser = False
        super(QueryTest, self).__init__(*args, **kwargs)

    def test_query_login_admin(self):
        with self.assertNumQueries(39 + 0*UserLog.is_enabled()):
            self.browser_login_admin()

    def test_query_login_teacher(self):
        """Check the # of queries when logging in as a teacher."""
        teacher = FacilityUser(is_teacher=True, username="t1", facility=self.facility, password="dummy")
        teacher.set_password("t1")
        teacher.save()

        with self.assertNumQueries(36 + 4*UserLog.is_enabled()):
            self.browser_login_teacher("t1", "t1", self.facility)

    def test_query_login_student(self):
        """Check the # of queries when logging in as a student."""
        student = FacilityUser(is_teacher=False, username="s1", facility=self.facility, password="dummy")
        student.set_password("s1")
        student.save()

        with self.assertNumQueries(40 + 4*UserLog.is_enabled()):
            self.browser_login_student("s1", "s1", self.facility)


    def test_query_status_admin(self):
        """"""
        self.test_query_login_admin()
        with self.assertNumQueries(7):
            self.browse_to(self.reverse("status"))

    def test_query_status_teacher(self):
        """"""
        self.test_query_login_teacher()
        with self.assertNumQueries(7):
            self.browse_to(self.reverse("status"))

    def test_query_status_student(self):
        """"""
        self.test_query_login_student()
        with self.assertNumQueries(7):
            self.browse_to(self.reverse("status"))


    def test_query_logout_admin(self):
        """"""
        self.test_query_login_admin()
        with self.assertNumQueries(14 + 0*UserLog.is_enabled()):
            self.browser_logout_user()

    def test_query_logout_teacher(self):
        """"""
        self.test_query_login_teacher()
        with self.assertNumQueries(13 + 27*UserLog.is_enabled()):
            self.browser_logout_user()

    def test_query_logout_student(self):
        """"""
        self.test_query_login_student()
        with self.assertNumQueries(13 + 27*UserLog.is_enabled()):
            self.browser_logout_user()


    def test_query_goto_math_logged_out(self):
        """Check the # of queries when browsing to the "Math" topic page"""

        # Without login
        with self.assertNumQueries(5):
            self.browse_to(self.live_server_url + "/math/")

    def test_query_goto_math_logged_in(self):
        """Check the # of queries when browsing to the "Math" topic page"""

        self.test_query_login_student()
        with self.assertNumQueries(7):
            self.browse_to(self.live_server_url + "/math/")
