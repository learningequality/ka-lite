"""
"""

import os
import shutil
import tempfile
import zipfile

from django.test import TestCase
from django.utils import unittest

import settings
from utils.testing import distributed_server_test
from utils.django_utils import call_command_with_output


@distributed_server_test
class InstallTestCase(TestCase):
    """Try out installation, packaging, and updating
    """
    def test_update(self):
        zip_file = tempfile.mkstemp()[1]
        os.remove(zip_file)
        self.assertFalse(os.path.exists(zip_file), "No zip file exists, to start.")

        install_dir = tempfile.mkdtemp()
        os.remove(install_dir)
        self.assertFalse(os.path.exists(zip_file), "No installation directory exists, to start.")

        # Make the package
        out = call_command_with_output("zip_kalite", file=zip_file, no_test=True, locale="en")
        self.assertEqual(out[1], '', "Command returns nothing on stderr")
        self.assertEqual(out[2], 0, "Command returns code 0")
        self.assertTrue(os.path.exists(zip_file), "Zip file exists.")

        # Unpack
        zipfile.ZipFile(zip_file)
        zip = zipfile.ZipFile(zip_file, "r")
        nfiles = len(zip.namelist())
        for fi,afile in enumerate(zip.namelist()):
            zip.extract(afile, path=install_dir)
        self.assertTrue(os.path.exists(install_dir), "Installation directory exists.")


        import pdb; pdb.set_trace()

