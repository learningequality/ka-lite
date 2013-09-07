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
# Implement sqlite PRAGMA using values in settings
#
def activate_pragma(sender, connection, **kwargs):

    if connection.vendor != 'sqlite':
        return
    try:
        # try: because target hardware may not have sqlite3
        import sqlite3
        if sqlite3.sqlite_version < "3.7":
            return
    except:
        return

    import settings
    cursor = connection.cursor()
    cursor.execute('PRAGMA synchronous=' + settings.SQLITE_PRAGMA_SYNCHRONOUS + ';')
    cursor.execute('PRAGMA journal_mode=' + settings.SQLITE_PRAGMA_JOURNAL_MODE + ';')
    if settings.SQLITE_PRAGMA_JOURNAL_MODE == 'WAL':
        cursor.execute('PRAGMA wal_autocheckpoint=' + str(settomgs.SQLITE_PRAGMA_WAL_AUTOCHECKPOINT) + ';')

from django.db.backends.signals import connection_created
connection_created.connect(activate_pragma)
#
#####
