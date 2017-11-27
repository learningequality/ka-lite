import logging
import os

from django.core.management import call_command

from .base import UpdatesTestCase
from kalite.topic_tools.settings import CONTENT_DATABASE_PATH
from tempfile import NamedTemporaryFile
from kalite.i18n.base import get_content_pack_url, delete_language
from fle_utils.internet.download import download_file


logger = logging.getLogger(__name__)


TEST_LANGUAGE = "zu"
TEST_CONTENT_DB = CONTENT_DATABASE_PATH.format(channel="khan", language=TEST_LANGUAGE)


class TestContentPack(UpdatesTestCase):
    """
    Test that topics with exercises are available, others are not.
    """

    def tearDown(self):
        UpdatesTestCase.tearDown(self)
        delete_language(TEST_LANGUAGE)


    def test_retrievecontentpack(self):
        """
        Tests that downloading and installing on of the smallest content packs
        (Zulu) works.
        """
        call_command("retrievecontentpack", "download", TEST_LANGUAGE)
        self.assertTrue(os.path.exists(
            TEST_CONTENT_DB
        ))

    
    def test_install_local_with_delete(self):
        fp = NamedTemporaryFile(suffix=".zip", delete=False)
        url = get_content_pack_url(TEST_LANGUAGE)
        download_file(url, fp=fp, callback=None)
        call_command("retrievecontentpack", "local", TEST_LANGUAGE, fp.name)
        self.assertTrue(os.path.exists(
            TEST_CONTENT_DB
        ))
        delete_language(TEST_LANGUAGE)
        self.assertFalse(os.path.exists(
            TEST_CONTENT_DB
        ))
