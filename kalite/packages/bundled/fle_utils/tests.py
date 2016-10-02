"""
Tests of utility functions.  Though they aren't part of the "main" app,
there's no other app to include them with!
"""
import os
import sys
sys.path += [os.path.realpath(os.path.join(os.path.dirname(__file__), '..'))]

import datetime
import os
import shutil
import sys
import tempfile
import unittest
from mock import patch, Mock
from unittest import TestCase

import fle_utils.videos as videos
from general import datediff, version_diff, ensure_dir


class DateDiffTestCase(TestCase):
    """
    Unit tests for datediff function
    """

    def test_units(self):
        """
        A single difference, tested across different units
        """
        d1 = datetime.datetime(2000, 1, 1)
        d2 = datetime.datetime(2004, 1, 1)  # test 4 years apart

        self.assertEqual(datediff(d2, d1, units="microsecond"), 1E6*60*60*24*(365*4 + 1), "4 years (with leap year), in microseconds")
        self.assertEqual(datediff(d2, d1, units="microseconds"), 1E6*60*60*24*(365*4 + 1), "4 years (with leap year), in microseconds")

        self.assertEqual(datediff(d2, d1), 60*60*24*(365*4 + 1), "4 years (with leap year), in seconds (default)")
        self.assertEqual(datediff(d2, d1, units="second"), 60*60*24*(365*4 + 1), "4 years (with leap year), in seconds")
        self.assertEqual(datediff(d2, d1, units="seconds"), 60*60*24*(365*4 + 1), "4 years (with leap year), in seconds")

        self.assertEqual(datediff(d2, d1, units="minute"), 60*24*(365*4 + 1), "4 years (with leap year), in minutes")
        self.assertEqual(datediff(d2, d1, units="minutes"), 60*24*(365*4 + 1), "4 years (with leap year), in minutes")

        self.assertEqual(datediff(d2, d1, units="hour"), 24*(365*4 + 1), "4 years (with leap year), in hours")
        self.assertEqual(datediff(d2, d1, units="hours"), 24*(365*4 + 1), "4 years (with leap year), in hours")

        self.assertEqual(datediff(d2, d1, units="day"), 365*4 + 1, "4 years (with leap year), in days")
        self.assertEqual(datediff(d2, d1, units="days"), 365*4 + 1, "4 years (with leap year), in days")

        self.assertEqual(datediff(d2, d1, units="week"), (365*4 + 1)/7., "4 years (with leap year), in weeks")
        self.assertEqual(datediff(d2, d1, units="weeks"), (365*4 + 1)/7., "4 years (with leap year), in weeks")

    def test_sign(self):
        """
        Test the diff in both directions, validate they are the same and of opposite signs.
        """
        d1 = datetime.datetime(2000, 1, 1, 0, 0, 0, 0)
        d2 = datetime.datetime(2000, 1, 1, 0, 0, 0, 1)  # test 4 years apart

        self.assertTrue(datediff(d1,d2) < 0, "First date earlier than the second returns negative.")
        self.assertTrue(datediff(d2,d1) > 0, "Second date earlier than the first returns positive.")
        self.assertTrue(datediff(d2,d2) == 0, "First date equals the second returns 0.")


class VersionDiffTestCase(TestCase):
    """
    Unit tests for version_diff
    """

    def test_sign(self):
        """
        Test the diff in both directions, validate they are the same and of opposite signs.
        """
        v1 = "0.1"
        v2 = "0.2"

        self.assertTrue(version_diff(v1, v2) < 0, "First version earlier than the second returns negative.")
        self.assertTrue(version_diff(v2, v1) > 0, "Second version earlier than the first returns positive.")
        self.assertTrue(version_diff(v2, v2) == 0, "First version equals the second returns 0.")

    def test_values(self):
        """
        Test a few different values for the difference
        """
        self.assertEqual(version_diff("0.1", "0.20"), -19, "abs(diff) > 10")

    def test_levels(self):
        """
        Test major, minor, and patch-level differences.
        """

        self.assertEqual(version_diff("1", "2"), -1, "Major version diff (no minor)")
        self.assertEqual(version_diff("1.0", "2.0"), -1, "Major version diff (matching minor)")

        self.assertEqual(version_diff("0.1", "0.2"), -1, "Minor version diff (no patch)")
        self.assertEqual(version_diff("0.1.0", "0.2.0"), -1, "Minor version diff (matching patch)")

        self.assertEqual(version_diff("0.0.1", "0.0.2"), -1, "Patch version diff (no sub-patch)")
        self.assertEqual(version_diff("0.0.1.0", "0.0.2.0"), -1, "Patch version diff (matching sub-patch)")


class EnsureDirTestCase(TestCase):
    """
    Unit tests for ensure_dir function
    """

    def setUp(self):
        self.dirname = tempfile.mkdtemp()
        self.filename = tempfile.mkstemp(dir=self.dirname)[1]

    def tearDown(self):
        if os.path.exists(self.dirname):
            shutil.rmtree(self.dirname)

    def assertDirExists(self, path):
        self.assertTrue(os.path.isdir(path))

    def assertNotExists(self, path):
        self.assertFalse(os.path.exists(path))

    def test_dir(self):
        ensure_dir(self.dirname)
        self.assertDirExists(self.dirname)

    def test_new_dir(self):
        newdir = os.path.join(self.dirname, 'newdir', 'newdir')
        self.assertNotExists(newdir)
        ensure_dir(newdir)
        self.assertDirExists(newdir)

    def test_new_dotted_dir(self):
        newdir = os.path.join(self.dirname, 'new.dir')
        self.assertNotExists(newdir)
        ensure_dir(newdir)
        self.assertDirExists(newdir)

    def test_file(self):
        if sys.version_info < (2,7):  # we don't even get skipIf in Python 2.6!
            return
        with self.assertRaisesRegexp(OSError, 'Not a directory'):
            ensure_dir(self.filename)

    def test_new_dir_after_file(self):
        if sys.version_info < (2,7):  # we don't even get skipIf in Python 2.6!
            return
        newdir = os.path.join(self.filename, 'newdir')
        with self.assertRaisesRegexp(OSError, 'Not a directory'):
            ensure_dir(newdir)
        self.assertNotExists(newdir)


class DownloadFileTests(TestCase):

    @patch("videos.delete_downloaded_files", Mock)
    @patch.object(videos, "delete_downloaded_files", Mock)
    @patch.object(videos, "download_file")
    def test_downloading_in_right_location(self, download_file_method):

        download_file_method.side_effect = [
            # During the download_file for videos
            (
                None,  # doesn't matter for this test.
                Mock(type="video"),  # so download_video will succeed.
            ),
            # For downloading images
            (
                None,
                Mock(type="image"),  # so download_video will succeed.
            )
        ]

        content_dir = "/tmp"
        content_file = "something.mp3"
        expected_path = os.path.join(content_dir, content_file)

        videos.download_video("something", content_dir, format="mp3")

        url, filepath, func = download_file_method.call_args_list[0][0]
        self.assertEqual(filepath, expected_path)

if __name__ == '__main__':
    sys.exit(unittest.main())
