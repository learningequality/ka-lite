# encoding: UTF-8
import getpass

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import Client, TestCase

from .. import get_installed_language_packs


class LanguageSwitchingTests(TestCase):

    TEST_LANGUAGES = ['de', 'it', 'pt-BR']

    ADMIN_USERNAME = 'testadmin'
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

        self.client = Client()

        self.admin = User.objects.create(username=self.ADMIN_USERNAME, password='nein')
        self.admin.set_password(self.ADMIN_PASSWORD)
        self.admin.save()

    def test_logged_out_homepage_language_switches_from_english_and_back(self):
        # response = self.client.get('/', data={'set_user_language': 'de'})
        foreign_language_text_mappings = {
            'de': "Durch Videos lernen",
            'it': "Un'educazione mondiale gratuita per chiunque ovunque",
            'pt-BR': "Uma educação sem salas de aula para qualquer um em qualquer lugar",
        }
        english_text = "A free world-class education for anyone anywhere"

        for lang_code, expected_text in foreign_language_text_mappings.iteritems():
            # switch to the foreign language
            response = self.client.get('/?set_user_language=%s' % lang_code, follow=True)
            self.assertIn(expected_text, response.content)

            # switch back to english, and test that we successfully switched back
            response = self.client.get('/?set_user_language=%s' % "en", follow=True)
            self.assertIn(english_text, response.content)
