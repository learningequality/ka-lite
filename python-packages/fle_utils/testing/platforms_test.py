'''
Tests for platforms.py
'''
import os
import platform
import shutil
import sys
import unittest

import mock
from mock import patch

sys.path += [os.path.realpath('..'), os.path.realpath('.')]

from ..platforms import system_script_extension, system_specific_unzipping

class SystemScriptExtensionTests(unittest.TestCase):

    @patch.object(platform, 'system')
    def test_returns_bat_on_windows(self, system_method):
        system_method.return_value = 'Windows'

        self.assertEquals(system_script_extension(), '.bat')
        self.assertEquals(system_script_extension('Windows'), '.bat')

    @patch.object(platform, 'system')
    def test_returns_command_on_darwin(self, system_method):
        system_method.return_value = 'Darwin' # the Mac kernel

        self.assertEquals(system_script_extension(), '.command')
        self.assertEquals(system_script_extension('Darwin'), '.command')

    @patch.object(platform, 'system')
    def test_returns_sh_on_linux(self, system_method):
        system_method.return_value = 'Linux'

        self.assertEquals(system_script_extension(), '.sh')
        self.assertEquals(system_script_extension('Linux'), '.sh')

    @patch.object(platform, 'system')
    def test_returns_sh_by_default(self, system_method):
        system_method.return_value = 'Random OS'

        self.assertEquals(system_script_extension(), '.sh')
        self.assertEquals(system_script_extension('Random OS'), '.sh')


class SystemSpecificUnzippingTests(unittest.TestCase):

    def setUp(self):
        self.dest_dir = os.path.join(os.path.dirname(__file__), 'extract_dir')

    def tearDown(self):
        shutil.rmtree(self.dest_dir, ignore_errors=True)

    def test_raises_exception_on_invalid_zipfile(self):
        with self.assertRaises(Exception):
            system_specific_unzipping(__file__, self.dest_dir)

    @patch.object(os, 'mkdir')
    @patch.object(os.path, 'exists')
    def test_if_dest_dir_created(self, exists_method, mkdir_method):
        exists_method.return_value = False

        try:
            system_specific_unzipping('nonexistent.zip', self.dest_dir)
        except:
            pass

        mkdir_method.assert_called_once_with(self.dest_dir)


if __name__ == '__main__':
    unittest.main()
