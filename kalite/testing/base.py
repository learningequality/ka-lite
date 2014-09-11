"""
Contains test wrappers and helper functions for
automated of KA Lite using selenium
for automated browser-based testing.
"""
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import Client, TestCase

from kalite.shared.decorators.misc import deprecated

from .client import KALiteClient
from .mixins.securesync_mixins import CreateDeviceMixin


@deprecated
def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""

    test_admin = User.objects.create_superuser(username, email, password)

    # You'll need to log him in before you can send requests through the client
    client = Client()
    assert client.login(username=test_admin.username, password=password)

    # set dummy password, so it can be passed around
    test_admin.password = password
    assert client.login(username=test_admin.username, password=password)

    return test_admin


class KALiteTestCase(CreateDeviceMixin, TestCase):
    """The base class for KA Lite test cases."""

    def setUp(self):
        self.setup_fake_device()

        super(KALiteTestCase, self).setUp()

    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name, args=args, kwargs=kwargs)


class KALiteClientTestCase(KALiteTestCase):

    def setUp(self):
        self.client = KALiteClient()
        self.client.setUp()

        super(KALiteClientTestCase, self).setUp()


class KALiteBrowserTestCase(KALiteTestCase):
    pass
