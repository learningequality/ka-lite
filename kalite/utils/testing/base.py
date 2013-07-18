"""
Contains test wrappers and helper functions for 
automated of KA Lite using selenium
for automated browser-based testing.
"""

from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase

from kalite import settings


def create_test_admin(username="admin", password="pass", email="admin@example.com"):
    """Create a test user.
    Taken from http://stackoverflow.com/questions/3495114/how-to-create-admin-user-in-django-tests-py"""
    
    test_admin = User.objects.create_superuser(username, email, password)
    settings.LOG.debug('Created user "%s"' % username)

    # You'll need to log him in before you can send requests through the client
    client = Client()
    assert client.login(username=test_admin.username, password=password)

    # set dummy password, so it can be passed around
    test_admin.password = password
    assert client.login(username=test_admin.username, password=password)
    
    return test_admin
    
    

class KALiteTestCase(LiveServerTestCase):
    """The base class for KA Lite test cases."""
    
    def __init__(self, *args, **kwargs):
        #create_test_admin()
        return super(KALiteTestCase, self).__init__(*args, **kwargs)
        
    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(url_name, args=args, kwargs=kwargs)

