"""
REF: http://stackoverflow.com/a/17966818/845481

locale.getlocale() problems on OSX
==================================
From here: Try adding or editing the ~/.profile or ~/.bash_profile file for it to correctly
export your locale settings upon initiating a new session.

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
"""

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
    NO_VERSION = "<no version>"

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

    def _fail(self, msg="", raise_fail=True, end_chars="\n"):
        self._log("%s %s%s" % (msg, self.FAIL, end_chars))
        if raise_fail:
            self.fail(msg)

    def _pass(self, msg="", end_chars="\n"):
        self._log("%s %s%s" % (msg, self.OK, end_chars,))

    def check_path(self, path, mode=os.W_OK, msg=None, delay=0, raise_fail=True, end_chars="\n"):
        try:
            self._log(msg, delay)
            is_ok = os.access(path, mode)
            if is_ok:
                self._pass(end_chars=end_chars)
                return True
            else:
                self._fail(raise_fail=raise_fail, end_chars=end_chars)
        except Exception as exc:
            msg = "%s access to %s path failed: %s" % (mode, path, exc,)
            self.fail(msg)
        return False

    def get_version(self, module):
        version = getattr(module, "version",
                          getattr(module, "__version__",
                                  getattr(module, "VERSION",
                                          getattr(module, "__VERSION__", self.NO_VERSION))))
        if isinstance(version, basestring):
            return version
        if isinstance(version, tuple):
            return _tuple_to_str(version)
        # attribute found is a python module like `youtube_dl.version`, so we recurse
        return self.get_version(version)


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
        "iso8601": NO_VERSION,
        "kaa": "0.99.2dev",
        "khan_api_python": NO_VERSION,
        "khanacademy": NO_VERSION,
        "playground": NO_VERSION,
        "postmark": "0.1.6",
        "pyasn1": "0.1.4",
        "pytz": "2012d",
        "requests": "0.14.2",
        "rsa": "3.1.1",
        "securesync": "0.12.0",
        "smmap": "0.8.2",
        "south": "0.7.6",
        "tastypie": "0.11.0",
        "unittest2": "0.7.1",
        "werkzeug": "0.8.3",
        "youtube_dl": "2014.02.21.1",
        "collections_local_copy": NO_VERSION,
        "memory_profiler": "0.26",
        "mimeparse": "0.1.4",
        "mock": "1.0.1",
        "oauth": "1.0",
        "pbkdf2": "1.3",
        "polib": "1.0.3",
        "six": "1.8.0",
    }
    apps = getattr(settings, "INSTALLED_APPS", [])

    def test_apps_are_importable(self):
        self._log("Testing if apps are importable...")
        fail_count = 0
        for app in self.apps:
            self._log("\n...importing %s..." % app)
            try:
                __import__(app)
                self._log(" %s" % self.OK)
            except ImportError as exc:
                fail_count += 1
                self._fail("Exception: %s..." % exc, raise_fail=False, end_chars="")
        if fail_count > 0:
            self._fail("\n...Result: %s app/s failed import..." % fail_count)
        else:
            self._pass("\n...Result: all apps can be imported...")

    def test_required_packages_and_versions(self):
        try:
            self._log("Testing required Python packages and their versions...")
            fail_count = 0
            for package, version in sorted(self.packages.iteritems()):
                self._log("\n...importing %s..." % package)
                p = __import__(package)
                imported_version = self.get_version(p)
                self._log("need version %s, found %s..." % (version, imported_version,))
                if version == imported_version:
                    self._log(" %s" % self.OK)
                else:
                    fail_count += 1
                    self._fail(raise_fail=False, end_chars="")
            if fail_count > 0:
                self._fail("\n...Result: %s required Python package/s failed import..." % fail_count)
            else:
                self._pass("\n...Result: all required Python packages can be imported...")
        except ImportError as exc:
            self._fail("Exception: %s" % exc)

    def test_packages_dependencies(self):
        logging.info("Testing dependencies of the required Python packages...")
        self.assertTrue(False)


class PathsTests(DependenciesTests):
    """
    Check that we have access to all paths and files we need read or write access to.
    """

    JSON_FILES = ("assessmentitems.json", "channel_data.json", "content.json", "contents.json", "exercises.json",
                  "map_domains.json", "map_subjects.json", "map_topics.json", "map_tutorials.json",
                  "topic_hierarchy.json", "topics.json", "videos.json",)

    def test_database_path(self):
        sqlite_path = settings.DATABASES["default"]["NAME"]
        msg = 'Testing write access to SQLite3 database "%s"...' % sqlite_path
        self.check_path(sqlite_path, os.W_OK, msg=msg, delay=1)

    def test_content_path(self):
        content_path = os.path.realpath(os.path.join(PROJECT_PATH, "content"))
        msg = 'Testing write access to content folder "%s"...' % content_path
        self.check_path(content_path, os.W_OK, msg=msg)

    def test_data_path(self):
        khan_path = os.path.realpath(os.path.join(PROJECT_PATH, "data", "khan"))
        msg = 'Testing read-only access to data folder "%s"...' % khan_path
        self.check_path(khan_path, os.R_OK, msg=msg)

    def test_json_path(self):
        khan_path = os.path.realpath(os.path.join(PROJECT_PATH, "data", "khan"))
        msg = 'Testing access to and format of json files at "%s"...' % khan_path
        self._log(msg)
        fail_count = 0
        for json_file in self.JSON_FILES:
            json_path = os.path.realpath(os.path.join(khan_path, json_file)) + ''
            msg = '\n...checking access to "%s"...' % json_path
            if not self.check_path(json_path, os.R_OK, msg=msg, raise_fail=False, end_chars=""):
                fail_count += 1
            else:
                # attempt to load .json file to validate format
                self._log("\n......loading json file...")
                from fle_utils.general import softload_json
                json_content = softload_json(json_path)
                if json_content == {}:
                    msg = "file has invalid json format or is empty..."
                    self._fail(msg, raise_fail=False, end_chars="")
                    fail_count += 1
                else:
                    self._pass(end_chars="")
        if fail_count > 0:
            self._fail("\n...Result: %s json file/s failed test..." % fail_count)
        else:
            self._pass("\n...Result: all json file/s are ok...")

    def test_scripts_path(self):
        scripts_path = os.path.realpath(os.path.join(PROJECT_PATH, "scripts"))
        msg = 'Testing execute access for the scripts folder "%s"...' % scripts_path
        self.check_path(scripts_path, os.X_OK, msg=msg)


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
