import requests
import zipfile
from cStringIO import StringIO
from mock import patch, MagicMock, call

from kalite.i18n import get_language_pack_url
from kalite.i18n.management.commands import create_dummy_language_pack as mod
from kalite.testing.base import KALiteTestCase


class CreateDummyLanguagePackCommandTests(KALiteTestCase):
    pass


class CreateDummyLanguagePackUtilityFunctionTests(KALiteTestCase):

    @patch.object(requests, "get", autospec=True)
    def test_download_language_pack(self, get_method):

        # so the next n lines before a newline separator are all about
        # creating a dummy zipfile that is readable by zipfile.ZipFile
        dummy_file = StringIO()
        zf = zipfile.ZipFile(dummy_file, mode="w")
        zf.close()
        get_method.return_value.content = dummy_file.getvalue()  # should still be convertible to a zipfile

        lang = "dummylanguage"
        result = mod.download_language_pack(lang)

        get_method.assert_called_once_with(get_language_pack_url(lang))
        self.assertIsInstance(result, zipfile.ZipFile)


    def test_retrieve_mo_files(self):
        dummy_lang_pack = MagicMock(autospec=zipfile.ZipFile)

        result = mod.retrieve_mo_files(dummy_lang_pack)

        dummy_lang_pack.call_args_list == [call("LC_MESSAGES/django.mo"),
                                           call("LC_MESSAGES/djangojs.mo")]
        self.assertIsInstance(result, tuple)
