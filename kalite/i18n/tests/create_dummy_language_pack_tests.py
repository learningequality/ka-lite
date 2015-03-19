import accenting
import requests
import zipfile
from cStringIO import StringIO
from mock import patch, MagicMock, call, mock_open

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
        zf.write(__file__)      # write the current file into the zipfile, just so we have something in here
        zf.close()
        get_method.return_value.content = dummy_file.getvalue()  # should still be convertible to a zipfile

        lang = "dummylanguage"
        result = mod.download_language_pack(lang)

        get_method.assert_called_once_with(get_language_pack_url(lang))
        self.assertIsInstance(result, zipfile.ZipFile)


    def test_retrieve_mo_files(self):
        dummy_lang_pack = MagicMock(autospec=zipfile.ZipFile)

        result = mod.retrieve_mo_files(dummy_lang_pack)

        self.assertTrue(dummy_lang_pack.read.call_args_list == [call("LC_MESSAGES/django.mo"),
                                                                call("LC_MESSAGES/djangojs.mo")])
        self.assertIsInstance(result, tuple)


    @patch("accenting.convert_msg")
    @patch("polib.mofile", create=True)
    def test_create_mofile_with_dummy_strings(self, mofile_class, convert_msg_method):
        """
        Check if it writes to a file, and if it calls convert_msg
        """
        with patch('%s.open' % mod.__name__, mock_open(), create=True) as mopen:
            dummycontent = "writethis"
            dummylocation = "/this/doesnt/exist"
            mofile_class.return_value.__iter__ = MagicMock(return_value=iter([MagicMock(), MagicMock(), MagicMock()]))  # 3 "MOEntries"
            mofile_class.save = MagicMock()  # so we can simulate a save call

            mod.create_mofile_with_dummy_strings(dummycontent, dummylocation)

            self.assertTrue(mopen.call_args_list == [call(mod.TARGET_LANGUAGE_METADATA_PATH, 'w'),
                                                     call(dummylocation, 'w')])
            self.assertEqual(convert_msg_method.call_count, 3)
            mofile_class.return_value.save.assert_called_once_with(fpath=dummylocation)
