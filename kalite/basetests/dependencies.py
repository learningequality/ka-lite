import logging
import os
import sys

if __name__ == '__main__':
    # Make sure we have access to the `python-packages` folder of the project.
    PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
    PROJECT_PYTHON_PATHS = [
        os.path.join(PROJECT_PATH, "..", ".."),
        os.path.join(PROJECT_PATH, "..", "..", "kalite"),
        os.path.join(PROJECT_PATH, "..", "..", "python-packages"),
    ]
    sys.path = [os.path.realpath(p) for p in PROJECT_PYTHON_PATHS] + sys.path


import unittest2
import django
import kalite

# set environment variable for django's settings
os.environ["DJANGO_SETTINGS_MODULE"] = "kalite.settings"


# Custom logging functions so we can customize the output.
def _log(msg, delay=0):
    sys.stdout.write(msg)
    sys.stdout.flush()  # REF: https://answers.yahoo.com/question/index?qid=20110506145612AA1oU5Q
    if delay:
        import time
        time.sleep(delay)


def _fail(msg=None):
    if msg:
        _log(msg)
    else:
        _log("FAIL!\n")


def _pass(msg=None):
    if msg:
        _log(msg)
    else:
        _log("OK!\n")


class SqliteTests(unittest2.TestCase):
    """
    For versions of Python 2.5 or newer that include sqlite3 in the standard library Django will now use a
    pysqlite2 interface in preference to sqlite3 if it finds one is available.

    REF: https://docs.djangoproject.com/en/1.5/ref/databases/#using-newer-versions-of-the-sqlite-db-api-2-0-driver
    """

    def test_sqlite_is_installed(self):
        try:
            _log("Testing if SQLite3 is installed...", 1)
            import sqlite3
            _pass()
        except ImportError:
            _fail()

    def test_sqlite_version(self):
        _log("Testing SQLite3 version...", 1)
        _pass()
        # self.assertTrue(False)

    def test_sqlite_path_is_writable(self):
        try:
            from django.conf import settings
            sqlite_path = settings.DATABASES["default"]["NAME"]
            msg = 'Testing writable SQLite3 database "%s"...' % sqlite_path
            try:
                _log(msg, 1)
                is_ok = os.access(sqlite_path, os.W_OK)
                if is_ok:
                    _pass()
                else:
                    _fail()
            except Exception as exc:
                msg = "SQLite database path is not writable: %s" % exc
                logging.critical(msg)
                self.fail(msg)
        except ImportError as exc:
            self.fail("Settings cannot be imported: %s" % exc)


class DjangoTests(unittest2.TestCase):

    def test_django_is_installed(self):
        logging.info("Testing if Django is installed...")
        self.assertTrue(False)

    def test_django_version(self):
        logging.info("Testing Django version...")
        self.assertTrue(False)

    def test_minimum_python_version(self):
        logging.info("Testing the minimum Python version based on the Django version to use...")
        self.assertTrue(False)


class PackagesTests(unittest2.TestCase):

    def test_packages_are_installed(self):
        logging.info("Testing if required Python packages are installed...")
        self.assertTrue(False)

    def test_packages_version(self):
        logging.info("Testing required Python packages versions...")
        self.assertTrue(False)


class PathsTests(unittest2.TestCase):
    """
    Check that we have access to all paths we need read or write access.
    """

    def test_sqlite_path(self):
        logging.info('Testing write access to SQLite3 database path...')
        self.assertTrue(False)

    def test_content(self):
        logging.info('Test read-only access to "content" folder...')
        self.assertTrue(False)


class VersionTests(unittest2.TestCase):
    """
    Checks versions of python, packages we need to run smoothly.
    """

    def test_python_version(self):
        logging.info('Testing minimum version of Python...')
        self.assertTrue(False)

    def test_django_version(self):
        logging.info('Test version of Django')
        self.assertTrue(False)


class TestHandler(logging.StreamHandler):

    def __init__(self):
        logging.Handler.__init__(self)

    @property
    def stream(self):
        """Use which ever stream sys.stderr is referencing."""
        return sys.stderr


test_cases = (SqliteTests, DjangoTests, VersionTests, PathsTests, PackagesTests)
# test_cases = (SqliteTests,)


def load_tests(loader, tests, pattern):
    suite = unittest2.TestSuite()
    for test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    return suite


if __name__ == '__main__':

    # Don't display any messages, we will customize the output.
    unittest2.main(verbosity=0)
