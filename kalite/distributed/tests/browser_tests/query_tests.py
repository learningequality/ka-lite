"""
These use a web-browser, along selenium, to simulate user actions.
"""
import random
import string

from django.conf import settings

from .base import KALiteDistributedWithFacilityBrowserTestCase
from kalite.facility.models import FacilityUser
from kalite.main.models import UserLog


#To test range of query numbers.
#TODO: Put in more general location.
class FuzzyInt(int):
    def __new__(cls, lowest, highest):
        obj = super(FuzzyInt, cls).__new__(cls, highest)
        obj.lowest = lowest
        obj.highest = highest
        return obj

    def __eq__(self, other):
        return other >= self.lowest and other <= self.highest

    def __repr__(self):
        return "[%d..%d]" % (self.lowest, self.highest)

    def __str__(self):
        return self.__repr__()

    def __unicode__(self):
        return self.__repr__()

    def __format__(self, formatstr):
        return self.__repr__()

    def __add__(self, x):
        val = super(FuzzyInt, self).__add__(x)
        self.lowest += x
        self.highest += x
        return self


class QueryTest(KALiteDistributedWithFacilityBrowserTestCase):
    """"""
    def __init__(self, *args, **kwargs):
        """To guarantee state across tests, clear browser state every time."""
        random.seed('ben') # to make password reproducible
        self.persistent_browser = False
        super(QueryTest, self).__init__(*args, **kwargs)

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

        with self.assertNumQueries(FuzzyInt(25, 28) + 3 * UserLog.is_enabled()):
            self.browser_login_teacher("t1", passwd, self.facility)

    def test_query_login_student(self):
        """Check the # of queries when logging in as a student."""
        student = FacilityUser(is_teacher=False, username="s1", facility=self.facility)
        passwd = self._gen_valid_password()
        student.set_password(passwd)
        student.save()

        expected_num_queries = 25 + 3*UserLog.is_enabled()
        with self.assertNumQueries(FuzzyInt(expected_num_queries - 3, expected_num_queries + 3)):
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
        with self.assertNumQueries(0):
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
        with self.assertNumQueries(0):
            self.browse_to(self.live_server_url + "/math/")
