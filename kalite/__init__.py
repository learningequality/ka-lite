# testing isn't always available; just ignore if not
try:
    import shared.testing.testrunner
except Exception as e:
    pass
try:
    import tests.loadtesting as loadtesting
except Exception as e:
    pass


import version
VERSION = version.VERSION

try:
    import platform
    OS = ", ".join(platform.uname() + ("Python %s" % platform.python_version(),))
except:
    try:
        import sys
        OS = sys.platform
    except:
        OS = ""

#####
#
# Implement sqlite PRAGMA from settings
#
def activate_pragma(sender, connection, **kwargs):
    try:
        # try: because target hardware may not have sqlite3
        import sqlite3
        if sqlite3.sqlite_version < "3.7":
            return False
    except:
        return False
    if connection.vendor == 'sqlite':
        from settings import SQLITE_PRAGMA_SYNCHRONOUS
        from settings import SQLITE_PRAGMA_JOURNAL_MODE
        from settings import SQLITE_PRAGMA_AUTOCHECKPOINT
        print SQLITE_PRAGMA_SYNCHRONOUS, SQLITE_PRAGMA_JOURNAL_MODE, str(SQLITE_PRAGMA_AUTOCHECKPOINT)
        cursor = connection.cursor()
        cursor.execute('PRAGMA synchronous=' + SQLITE_PRAGMA_SYNCHRONOUS + ';')
        cursor.execute('PRAGMA journal_mode=' + SQLITE_PRAGMA_JOURNAL_MODE + ';')
        cursor.execute('PRAGMA wal_autocheckpoint=' + str(SQLITE_PRAGMA_AUTOCHECKPOINT) + ';')

from django.db.backends.signals import connection_created
connection_created.connect(activate_pragma)
#
#####
