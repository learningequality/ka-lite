import logging
import os
import sys

if __name__ == '__main__':
    # Make sure we have access to the python packages.
    PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
    PROJECT_PYTHON_PATHS = [
        os.path.join(PROJECT_PATH, "..", "..", "python-packages"),  # libraries (python-packages)
    ]
    sys.path = [os.path.realpath(p) for p in PROJECT_PYTHON_PATHS] + sys.path

import unittest2


class SqliteTests(unittest2.TestCase):
    """
    For versions of Python 2.5 or newer that include sqlite3 in the standard library Django will now use a
    pysqlite2 interface in preference to sqlite3 if it finds one is available.

    REF: https://docs.djangoproject.com/en/1.5/ref/databases/#using-newer-versions-of-the-sqlite-db-api-2-0-driver
    """

    def test_sqlite_is_installed(self):
        logging.info("Testing if SQLite3 is installed...")
        try:
            import sqlite3
        except ImportError:
            self.fail("SQLite3 is not installed.")

    def test_sqlite_version(self):
        logging.info("Testing SQLite3 version...")
        self.assertEqual(True, False)

    def test_sqlite_path_is_writable(self):
        logging.info("Testing SQLite3 path is writable...")
        self.assertEqual(True, False)


class DjangoTests(unittest2.TestCase):

    def test_django_is_installed(self):
        logging.info("Testing if Django is installed...")
        self.assertEqual(True, False)

    def test_django_version(self):
        logging.info("Testing Django version...")
        self.assertEqual(True, False)

    def test_minimum_python_version(self):
        logging.info("Testing the minimum Python version based on the Django version to use...")
        self.assertEqual(True, False)


class PackageTests(unittest2.TestCase):

    def test_packages_are_installed(self):
        logging.info("Testing if required Python packages are installed...")
        self.assertEqual(True, False)

    def test_packages_version(self):
        logging.info("Testing required Python packages versions...")
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest2.main()
