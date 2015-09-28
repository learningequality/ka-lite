"""
This module is for running a screenshot server (internal FLE purpose mainly).
To use it, run kalite with --settings=kalite.project.settings.screenshots or
set then environment variable DJANGO_SETTINGS_MODULE to
'kalite.project.settings.screenshots'.
"""
from .base import *  # @UnusedWildImport

SCREENSHOTS_OUTPUT_PATH = os.path.join(USER_DATA_ROOT, "data", "screenshots")
SCREENSHOTS_EXTENSION = ".png"

SCREENSHOTS_JSON_PATH = os.path.join(os.path.dirname(__file__), "data")
SCREENSHOTS_JSON_FILE = os.path.join(SCREENSHOTS_JSON_PATH, 'screenshots.json')
SQLITE3_ENGINE = 'django.db.backends.sqlite3'

INCLUDE_QTIP = True

# use another sqlite3 database for the screenshots
DATABASES = {
    'default': {
        "ENGINE": SQLITE3_ENGINE,
        "NAME": ":memory:",
    },
    "assessment_items": {
        "ENGINE": SQLITE3_ENGINE,
        "NAME": ":memory:",
    },
}
