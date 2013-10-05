"""
Tests of utility functions.  Though they aren't part of the "main" app,
there's no other app to include them with!
"""
import datetime

from django.test import TestCase

from utils.general import datediff, version_diff


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
