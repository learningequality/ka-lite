"""

New settings pattern

See:
https://github.com/learningequality/ka-lite/issues/4054
https://github.com/learningequality/ka-lite/issues/3757

All settings for the topic_tools app should be defined here, they can
only on django.conf.settings
"""
import os
from django.conf import settings

from kalite import ROOT_DATA_PATH

# OUTDATED - Special setting for Khan Academy content, was only used for
# assessment item unpacking. All assessment items have been moved from this
# location in distributed.management.commands.setup
OLD_ASSESSMENT_ITEMS_LOCATION = os.path.join(settings.CONTENT_ROOT, "khan")


# Are assessment items distributed in the system-wide data directory?
if settings.ASSESSMENT_ITEMS_SYSTEM_WIDE:
    ASSESSMENT_ITEM_ROOT = os.path.join(ROOT_DATA_PATH, 'assessment')
    KHAN_ASSESSMENT_ITEM_ROOT = os.path.join(ASSESSMENT_ITEM_ROOT, 'khan')
else:
    # Where assessment items are stored in general (but no additional channels
    # exist yet so it's all hard-coded for KHAN_ASSESSMENT_ITEM_ROOT below)
    ASSESSMENT_ITEM_ROOT = os.path.join(settings.CONTENT_ROOT, 'assessment')
    
    if not os.path.exists(ASSESSMENT_ITEM_ROOT):
        os.mkdir(ASSESSMENT_ITEM_ROOT)
    
    KHAN_ASSESSMENT_ITEM_ROOT = os.path.join(ASSESSMENT_ITEM_ROOT, 'khan')
    if not os.path.exists(KHAN_ASSESSMENT_ITEM_ROOT):
        os.mkdir(KHAN_ASSESSMENT_ITEM_ROOT)

# This one should always the settings because it is part of settings.DATABASES
KHAN_ASSESSMENT_ITEM_DATABASE_PATH = settings.DATABASES['assessment_items']['NAME']

# Default locations of specific elements from the assessment items bundle.
# Files will be forced into this location when running unpack_assessment_zip
KHAN_ASSESSMENT_ITEM_VERSION_PATH = os.path.join(KHAN_ASSESSMENT_ITEM_ROOT, 'assessmentitems.version')
KHAN_ASSESSMENT_ITEM_JSON_PATH = os.path.join(KHAN_ASSESSMENT_ITEM_ROOT, 'assessmentitems.json')
