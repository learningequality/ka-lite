import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.translation import ugettext as _

logging = settings.LOG


class Command(BaseCommand):

    def usage(self, argname):
        return """check_dependencies
        Check dependencies of the project on the current install."""

    def handle(self, *args, **options):
        self.check_sqlite()
        self.check_django()
        self.check_minimum_python_version()
        self.check_paths()

    def _log(self, msg, is_ok=False):
        status = _("OK.")
        if not is_ok:
            status = _("FAILED!")
        logging.info("%-120s %s" % (msg, status,))

    def _log_ok(self, msg):
        self._log(msg, is_ok=True)

    def _log_fail(self, msg):
        self._log(msg, is_ok=False)

    def check_sqlite(self):
        """
        For versions of Python 2.5 or newer that include sqlite3 in the standard library Django will now use a
        pysqlite2 interface in preference to sqlite3 if it finds one is available.

        REF: https://docs.djangoproject.com/en/1.5/ref/databases/#using-newer-versions-of-the-sqlite-db-api-2-0-driver
        """

        # Can we import sqlite3?
        msg = _("Testing if SQLite3 is installed")
        try:
            import sqlite3
            self._log_ok(msg)
        except ImportError:
            self._log_fail(msg)

        # TODO(cpauya): Is sqlite3 path writable?
        sqlite_path = settings.DATABASES["default"]["NAME"]
        msg = _('Testing writable SQLite3 database "%s"...') % sqlite_path
        try:
            is_ok = os.access(sqlite_path, os.W_OK)
            self._log(msg, is_ok=is_ok)
        except Exception:
            self._log_fail(msg)

    def check_django(self):
        self._log_fail("Testing django...")
        pass

    def check_minimum_python_version(self):
        self._log_fail("Testing minimum Python version based on Django version used...")
        pass

    def check_paths(self):
        self._log_fail("Testing paths...")
        pass
