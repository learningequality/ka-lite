"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import Client

from kalite.testing.base import KALiteTestCase
from kalite.testing.mixins.django_mixins import CreateAdminMixin

import importlib


class UrlTestCases(KALiteTestCase):
    """Walk through a set of URLs, and validate very basic properties (status code, some text)
    A good test to weed out untested view/template errors"""

    def validate_url(self, url, status_code=200, find_str=None):
        resp = Client().get(url)
        self.assertEquals(resp.status_code, status_code, "%s (check status code=%d != %d)" % (url, status_code, resp.status_code))
        if find_str is not None:
            self.assertTrue(find_str in resp.content, "%s (check content)" % url)


    def test_urls(self):
        settings.DEBUG=False
        self.validate_url('/')
        self.validate_url(reverse('facility_user_signup'), status_code=302)
        self.validate_url('/learn/')
        self.validate_url('/content/', status_code=404)
        self.validate_url('/accounts/login/', status_code=404)
        self.validate_url('/accounts/register/', status_code=404)



class AllUrlsTest(CreateAdminMixin, KALiteTestCase):

    def setUp(self):
        super(AllUrlsTest, self).setUp()

        self.admin_data = {"username": "admin", "password": "admin"}
        self.admin = self.create_admin(**self.admin_data)

    def test_responses(self, allowed_http_codes=[200, 302, 400, 401, 404, 405],
            credentials={}, logout_url="", default_kwargs={}, quiet=False):
        """
        This is a very liberal test, we are mostly just concerned with making sure
        that no pages throw errors (500).
        Adapted from:
        http://stackoverflow.com/questions/14454001/list-all-suburls-and-check-if-broken-in-python#answer-19162337
        Test all pattern in root urlconf and included ones.
        Do GET requests only.
        A pattern is skipped if any of the conditions applies:
            - pattern has no name in urlconf
            - pattern expects any positinal parameters
            - pattern expects keyword parameters that are not specified in @default_kwargs
        If response code is not in @allowed_http_codes, fail the test.
        if @credentials dict is specified (e.g. username and password),
            login before run tests.
        If @logout_url is specified, then check if we accidentally logged out
            the client while testing, and login again
        Specify @default_kwargs to be used for patterns that expect keyword parameters,
            e.g. if you specify default_kwargs={'username': 'testuser'}, then
            for pattern url(r'^accounts/(?P<username>[\.\w-]+)/$'
            the url /accounts/testuser/ will be tested.
        If @quiet=False, print all the urls checked. If status code of the response is not 200,
            print the status code.
        """
        # Some URLs only use POST requests, exclude them here.
        url_blacklist = []
        module = importlib.import_module(settings.ROOT_URLCONF)
        if credentials or self.admin_data:
            credentials = credentials or self.admin_data
            self.client.login(**credentials)
        def check_urls(urlpatterns, prefix=''):
            for pattern in urlpatterns:
                if hasattr(pattern, 'url_patterns'):
                    # this is an included urlconf
                    new_prefix = prefix
                    if pattern.namespace:
                        new_prefix = prefix + (":" if prefix else "") + pattern.namespace
                    check_urls(pattern.url_patterns, prefix=new_prefix)
                params = {}
                skip = False
                regex = pattern.regex
                for url in url_blacklist:
                    if regex.match(url):
                        skip = True
                if regex.groups > 0:
                    # the url expects parameters
                    # use default_kwargs supplied
                    if regex.groups > len(regex.groupindex.keys()) \
                        or set(regex.groupindex.keys()) - set(default_kwargs.keys()):
                        # there are positional parameters OR
                        # keyword parameters that are not supplied in default_kwargs
                        # so we skip the url
                        skip = True
                    else:
                        for key in set(default_kwargs.keys()) & set(regex.groupindex.keys()):
                            params[key] = default_kwargs[key]
                if hasattr(pattern, "name") and pattern.name:
                    name = pattern.name
                else:
                    # if pattern has no name, skip it
                    skip = True
                    name = ""
                fullname = (prefix + ":" + name) if prefix else name
                if not skip:
                    url = reverse(fullname, kwargs=params)
                    response = self.client.get(url)
                    self.assertIn(response.status_code, allowed_http_codes,
                        "{url} gave status code {status_code}".format(
                            url=url, status_code=response.status_code))
                    # print status code if it is not 200
                    status = "" if response.status_code == 200 else str(response.status_code) + " "
                    if not quiet:
                        print(status + url)
                    if url == logout_url and credentials:
                        # if we just tested logout, then login again
                        self.client.login(**credentials)
                else:
                    if not quiet:
                        print("SKIP " + regex.pattern + " " + fullname)
        check_urls(module.urlpatterns)