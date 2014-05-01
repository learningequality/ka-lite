# encoding: UTF-8
from django.contrib.auth.models import User
from django.core.management import call_command

from .. import get_installed_language_packs
from kalite.distributed.tests.browser_tests.base import KALiteDistributedBrowserTestCase


class BrowserLanguageSwitchingTests(KALiteDistributedBrowserTestCase):

    TEST_LANGUAGES = ['de', 'it', 'pt-BR']

    ADMIN_USERNAME = 'testadmin1'
    ADMIN_PASSWORD = 'testpassword'
    ADMIN_EMAIL = 'test@test.com'

    # TODO (ARON): move useful utility to either a module or TestCase subclass
    def is_language_installed(self, lang_code, force_reload=True):
        return lang_code in get_installed_language_packs(force=force_reload)

    def install_language(self, lang_code):
        if not self.is_language_installed(lang_code):
            call_command('languagepackdownload', lang_code=lang_code)

    def setUp(self):
        for lang in self.TEST_LANGUAGES:
            self.install_language(lang)

        self.admin = User.objects.create(username=self.ADMIN_USERNAME, password='nein')
        self.admin.set_password(self.ADMIN_PASSWORD)
        self.admin.save()
        super(KALiteDistributedBrowserTestCase, self).setUp()

    def test_logged_out_homepage_language_switches_from_english_and_back(self):
        # response = self.client.get('/', data={'set_user_language': 'de'})
        foreign_language_text_mappings = {
            'de': "Eine kostenlose Weltklasse Bildung für jeden und überall",
            'it': "gratuita per chiunque ovunque",
            'pt-BR': "Uma educação sem salas de aula para qualquer um em qualquer lugar",
        }
        assert sorted(self.TEST_LANGUAGES) == sorted(foreign_language_text_mappings.keys())
        english_text = "A free world-class education for anyone anywhere"

        for lang_code, expected_text in foreign_language_text_mappings.iteritems():
            self.browse_to(self.reverse("homepage"))
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % lang_code).click()
            self.assertIn(expected_text, self.browser.find_element_by_css_selector(".main-headline").text)

            # switch back to english, and test that we successfully switched back
            self.browser.find_element_by_css_selector("#language_selector > option[value='%s']" % "en").click()
            self.assertIn(english_text, self.browser.find_element_by_css_selector(".main-headline").text)
