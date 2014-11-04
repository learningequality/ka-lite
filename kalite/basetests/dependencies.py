import logging
import os
import sys

THIS_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_PATH = os.path.realpath(os.path.join(THIS_PATH, "..", ".."))

if __name__ == '__main__':
    # Make sure we have access to the `python-packages` folder of the project.
    PROJECT_PYTHON_PATHS = [
        os.path.join(PROJECT_PATH),
        os.path.join(PROJECT_PATH, "kalite"),
        os.path.join(PROJECT_PATH, "python-packages"),
    ]
    sys.path = [os.path.realpath(p) for p in PROJECT_PYTHON_PATHS] + sys.path

import unittest2

# set environment variable for django's settings
os.environ["DJANGO_SETTINGS_MODULE"] = "kalite.settings"

from django.conf import settings


def _tuple_to_str(t, delim="."):
    return delim.join(str(i) for i in t)


class DependenciesTests(unittest2.TestCase):
    """
    Base class for checking dependencies.

    Have a map of python and sqlite3 versions per django version released.

    TODO(cpauya): i18n for strings?
    """
    NO_VERSION = "-.-.-"

    DJANGO_VERSION = (1, 5, 1,)  # TODO(cpauya): get from our django package
    DJANGO_VERSION_STR = _tuple_to_str(DJANGO_VERSION)

    DJANGO_PRODUCTION_PORT = getattr(settings, "PRODUCTION_PORT", 8008)

    # REF: https://docs.djangoproject.com/en/1.5/releases/1.5/#python-compatibility
    MINIMUM_PYTHON_VERSION = (2, 6, 5,)
    MINIMUM_PYTHON_VERSION_STR = _tuple_to_str(MINIMUM_PYTHON_VERSION)

    # REF: https://docs.djangoproject.com/en/1.5/ref/databases/#sqlite-3-3-6-or-newer-strongly-recommended
    MINIMUM_SQLITE_VERSION = (3, 3, 6,)
    MINIMUM_SQLITE_VERSION_STR = _tuple_to_str(MINIMUM_SQLITE_VERSION)

    OK = "OK!"
    FAIL = "FAIL!"

    # Custom logging functions so we can customize the output.
    def _log(self, msg, delay=0):
        sys.stdout.write(msg)
        sys.stdout.flush()  # REF: https://answers.yahoo.com/question/index?qid=20110506145612AA1oU5Q
        if delay:  # delay in seconds
            import time
            time.sleep(delay)

    def _fail(self, msg="", raise_fail=True):
        self._log("%s %s\n" % (msg, self.FAIL,))
        if raise_fail:
            self.fail(msg)

    def _pass(self, msg=OK):
        self._log(" %s\n" % msg)

    def check_path(self, path, mode=os.W_OK, msg=None, delay=0):
        try:
            self._log(msg, delay)
            is_ok = os.access(path, mode)
            if is_ok:
                self._pass()
            else:
                self._fail()
        except Exception as exc:
            msg = "%s access to %s path failed: %s" % (mode, path, exc,)
            self.fail(msg)

    def get_version(self, module):
        version = getattr(module, "version",
                          getattr(module, "__version__",
                                  getattr(module, "VERSION",
                                          getattr(module, "__VERSION__", self.NO_VERSION))))
        return version


class SqliteTests(DependenciesTests):
    """
    For versions of Python 2.5 or newer that include sqlite3 in the standard library Django will now use a
    pysqlite2 interface in preference to sqlite3 if it finds one is available.

    REF: https://docs.djangoproject.com/en/1.5/ref/databases/#using-newer-versions-of-the-sqlite-db-api-2-0-driver
    """

    def test_if_sqlite_is_installed(self):
        try:
            self._log("Testing if SQLite3 is installed...")
            import sqlite3
            self._pass()
        except ImportError:
            self._fail()

    def test_minimum_sqlite_version(self):
        self._log("Testing minimum SQLite3 version %s for Django version %s..." %
                  (self.MINIMUM_SQLITE_VERSION_STR, self.DJANGO_VERSION_STR,))
        from sqlite3 import sqlite_version_info
        if self.MINIMUM_SQLITE_VERSION <= sqlite_version_info:
            self._pass()
        else:
            self._fail()

    def test_sqlite_path_is_writable(self):
        sqlite_path = settings.DATABASES["default"]["NAME"]
        msg = 'Testing writable SQLite3 database "%s"...' % sqlite_path
        self.check_path(sqlite_path, os.W_OK, msg=msg)


class DjangoTests(DependenciesTests):

    def test_django_is_installed(self):
        self._log("Testing if Django is installed...")
        try:
            import django
            self._pass()
        except ImportError:
            self._fail()

    def test_django_version(self):
        self._log("Testing Django %s version..." % self.DJANGO_VERSION_STR)
        try:
            from django.utils.version import get_version
            if get_version() == self.DJANGO_VERSION_STR:
                self._pass()
            else:
                self._fail(" found version %s instead..." % get_version())
        except ImportError:
            self._fail()

    def test_minimum_python_version(self):
        self._log("Testing minimum Python version %s for Django version %s..." %
                  (self.MINIMUM_PYTHON_VERSION_STR, self.DJANGO_VERSION_STR,))
        if sys.version_info >= self.MINIMUM_PYTHON_VERSION:
            self._pass()
        else:
            self._fail(" found version %s instead..." % (_tuple_to_str(sys.version_info),))

    def test_django_can_serve_on_port(self):
        self._log("Testing if Django can serve on production port %s..." % self.DJANGO_PRODUCTION_PORT)
        from django.core.management import call_command
        # self._log('calling command "kaserve"...')
        # result = call_command("kaserve")
        # self._log('result %s...' % result)
        self._fail()
        self.assertTrue(False)


class PackagesTests(DependenciesTests):

    # make a dictionary of package and it's version?
    NO_VERSION = DependenciesTests.NO_VERSION
    # TODO(cpauya): add more packages from `python-packages` here
    packages = {
        "announcements": "1.0.2",
        "annoying": NO_VERSION,
        "async": NO_VERSION,
        "cherrypy": "3.2.2",
        "dateutil": "1.5",
        "debug_toolbar": "unknown",
        "decorator": NO_VERSION,
        "django": "1.5.1.final.0",
        "django_extensions": "1.0.1",
        "django_snippets": "1.0.1",
        "fle_utils": NO_VERSION,
        "git": "0.3.2 RC1",
        "gitdb": "0.5.4",
        "httplib2": "0.8",
        "ifcfg": NO_VERSION,
        "importlib": NO_VERSION,
        "iso8601": NO_VERSION
    }
    apps = getattr(settings, "INSTALLED_APPS", [])

    def test_apps_are_importable(self):
        try:
            self._log("Testing if apps are importable...")
            for app in self.apps:
                self._log("\n...importing %s..." % app)
                __import__(app)
                self._log("%s" % self.OK)
            self._pass("\n...all apps can be imported... %s" % self.OK)
        except ImportError as exc:
            self._fail("Exception: %s" % exc)

    def test_required_packages_and_versions(self):
        try:
            self._log("Testing required Python packages and their versions...")
            for package, version in self.packages.iteritems():
                self._log("\n...importing %s..." % package)
                p = __import__(package)
                imported_version = self.get_version(p)
                if isinstance(imported_version, tuple):
                    imported_version = _tuple_to_str(imported_version)
                self._log("version %s == %s..." % (version, imported_version,))
                self.assertEqual(version, imported_version)
                self._log(self.OK)
            self._pass("\n...all required Python packages can be imported... %s" % self.OK)
        except ImportError as exc:
            self._fail("Exception: %s" % exc)

    def test_packages_dependencies(self):
        logging.info("Testing dependencies of the required Python packages...")
        self.assertTrue(False)


class PathsTests(DependenciesTests):
    """
    Check that we have access to all paths we need read or write access to.
    """

    def test_database_path(self):
        sqlite_path = settings.DATABASES["default"]["NAME"]
        msg = 'Testing writable SQLite3 database "%s"...' % sqlite_path
        self.check_path(sqlite_path, os.W_OK, msg=msg, delay=1)

    def test_content_path(self):
        content_path = os.path.realpath(os.path.join(PROJECT_PATH, "content"))
        msg = 'Testing read-only access to content folder "%s"...' % content_path
        self.check_path(content_path, os.R_OK, msg=msg)

    def test_data_path(self):
        khan_path = os.path.realpath(os.path.join(PROJECT_PATH, "data", "khan"))
        msg = 'Testing read-only access to data folder "%s"...' % khan_path
        self.check_path(khan_path, os.R_OK, msg=msg)


test_cases = (SqliteTests, DjangoTests, PathsTests, PackagesTests)
# test_cases = (SqliteTests, DjangoTests,)


def load_tests(loader, tests, pattern):
    suite = unittest2.TestSuite()
    for test_case in test_cases:
        suite.addTests(loader.loadTestsFromTestCase(test_case))
    return suite


if __name__ == '__main__':

    # Don't display any messages, we will customize the output.
    unittest2.main(verbosity=0)
