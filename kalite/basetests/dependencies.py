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


def _tuple_to_str(t, delim="."):
    return delim.join(str(i) for i in t)


class DependenciesTests(unittest2.TestCase):
    """
    Have a map of python and sqlite3 versions per django version released.
    """

    DJANGO_VERSION = (1, 5, 1,)  # TODO(cpauya): get from our django package

    # REF: https://docs.djangoproject.com/en/1.5/releases/1.5/#python-compatibility
    MINIMUM_PYTHON_VERSION = (2, 6, 5,)

    # REF: https://docs.djangoproject.com/en/1.5/ref/databases/#sqlite-3-3-6-or-newer-strongly-recommended
    MINIMUM_SQLITE_VERSION = (3, 3, 6,)

    # Custom logging functions so we can customize the output.
    def _log(self, msg, delay=0):
        sys.stdout.write(msg)
        sys.stdout.flush()  # REF: https://answers.yahoo.com/question/index?qid=20110506145612AA1oU5Q
        if delay:
            import time
            time.sleep(delay)

    def _fail(self, msg=" FAIL!\n", raise_fail=True):
        self._log(msg)
        if raise_fail:
            self.fail(msg)

    def _pass(self, msg=" OK!\n"):
        self._log(msg)


class SqliteTests(DependenciesTests):
    """
    For versions of Python 2.5 or newer that include sqlite3 in the standard library Django will now use a
    pysqlite2 interface in preference to sqlite3 if it finds one is available.

    REF: https://docs.djangoproject.com/en/1.5/ref/databases/#using-newer-versions-of-the-sqlite-db-api-2-0-driver
    """

    def test_sqlite_is_installed(self):
        try:
            self._log("Testing if SQLite3 is installed...", 1)
            import sqlite3
            self._pass()
        except ImportError:
            self._fail()

    def test_minimum_sqlite_version(self):
        self._log("Testing minimum SQLite3 version %s for Django version %s..." %
                  (_tuple_to_str(self.MINIMUM_SQLITE_VERSION), _tuple_to_str(self.DJANGO_VERSION),), 1)
        from sqlite3 import version_info
        if self.MINIMUM_SQLITE_VERSION <= version_info:
            self._pass()
        else:
            self._fail()

    def test_sqlite_path_is_writable(self):
        try:
            from django.conf import settings
            sqlite_path = settings.DATABASES["default"]["NAME"]
            msg = 'Testing writable SQLite3 database "%s"...' % sqlite_path
            try:
                self._log(msg, 1)
                is_ok = os.access(sqlite_path, os.W_OK)
                if is_ok:
                    self._pass()
                else:
                    self._fail(self)
            except Exception as exc:
                msg = "SQLite database path is not writable: %s" % exc
                logging.critical(msg)
                self.fail(msg)
        except ImportError as exc:
            self.fail("Settings cannot be imported: %s" % exc)


class DjangoTests(DependenciesTests):

    def test_django_is_installed(self):
        self._log("Testing if Django is installed...", 1)
        try:
            import django
            self._pass()
        except ImportError:
            self._fail(self)

    def test_django_version(self):
        self._log("Testing Django %s version..." % _tuple_to_str(self.DJANGO_VERSION), 1)
        try:
            from django.utils.version import get_version
            self._pass()
        except ImportError:
            self._fail(self)

    def test_minimum_python_version(self):
        self._log("Testing minimum Python version %s for Django version %s..." %
                  (_tuple_to_str(self.MINIMUM_PYTHON_VERSION), _tuple_to_str(self.DJANGO_VERSION),), 1)
        if sys.version_info >= self.MINIMUM_PYTHON_VERSION:
            self._pass()
        else:
            self._fail(self)


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
test_cases = (SqliteTests, DjangoTests,)


def load_tests(loader, tests, pattern):
    suite = unittest2.TestSuite()
    for test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    return suite


if __name__ == '__main__':

    # Don't display any messages, we will customize the output.
    unittest2.main(verbosity=0)
