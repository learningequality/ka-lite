# encoding: UTF-8
import logging
import time

from django.contrib.auth.models import User
from django.core.management import call_command

from .. import get_installed_language_packs
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase
from kalite.i18n.tests.base import I18nTestCase


class BrowserLanguageSwitchingTests(KALiteDistributedBrowserTestCase, I18nTestCase):

    TEST_LANGUAGES = ['it', 'pt-BR']

    ADMIN_USERNAME = 'testadmin1'
    ADMIN_PASSWORD = 'testpassword'
    ADMIN_EMAIL = 'test@test.com'

    def setUp(self):
        self.admin = User.objects.create(username=self.ADMIN_USERNAME, password='nein')
        self.admin.set_password(self.ADMIN_PASSWORD)
        self.admin.save()

        self.foreign_language_homepage_text_mappings = {
            'it': "gratuita per chiunque ovunque",
            'pt-BR': "Uma educação sem salas de aula para qualquer um em qualquer lugar",
        }
        assert sorted(self.TEST_LANGUAGES) == sorted(self.foreign_language_homepage_text_mappings.keys())

        super(KALiteDistributedBrowserTestCase, self).setUp()
        self.install_languages()

    def tearDown(self):
        self.uninstall_languages()
        super(KALiteDistributedBrowserTestCase, self).tearDown()


    def test_logged_out_homepage_language_switches_from_english_and_back(self):
        # response = self.client.get('/', data={'set_user_language': 'de'})
        english_text = "A free world-class education for anyone anywhere"

        for lang_code, expected_text in self.foreign_language_homepage_text_mappings.iteritems():
            self.browse_to(self.reverse("homepage"))
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % lang_code).click()
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)

            # switch back to english, and test that we successfully switched back
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % "en").click()
            self.assertIn(english_text, self.browser.find_element_by_css_selector(".main-headline").text)


    def test_set_server_default_language(self):
        self.browser_login_admin()
        self.register_device()

        for lang, expected_text in self.foreign_language_homepage_text_mappings.iteritems():
            self.browse_to(self.reverse("update_languages"))
            self.browser.find_element_by_css_selector(".set_server_language[value='%s']" % lang).click()

            self.browse_to(self.reverse("homepage"))
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)
