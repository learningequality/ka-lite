from django.test import Client

from .base import I18nTestCase


class JSCatalogTests(I18nTestCase):

    TEST_LANGUAGES = ['de', 'it', 'pt-BR']

    def test_catalog_files_are_present(self):
        self.install_languages()
        client = Client()

        for lang in self.TEST_LANGUAGES:
            resp = client.get('/static/js/i18n/pl.js', follow=True)
            self.assertEqual(resp.status_code, 200, "Couldn't get %s.js: returned status %s" % (lang, resp.status_code))
