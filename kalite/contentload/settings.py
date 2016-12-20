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

# Where assessment items are stored in general (but no additional channels
# exist yet so it's all hard-coded for KHAN_ASSESSMENT_ITEM_ROOT below)
ASSESSMENT_ITEM_ROOT = os.path.join(settings.CONTENT_ROOT, 'assessment')

if not os.path.exists(ASSESSMENT_ITEM_ROOT):
    os.mkdir(ASSESSMENT_ITEM_ROOT)

KHAN_ASSESSMENT_ITEM_ROOT = os.path.join(ASSESSMENT_ITEM_ROOT, 'khan')
if not os.path.exists(KHAN_ASSESSMENT_ITEM_ROOT):
    os.mkdir(KHAN_ASSESSMENT_ITEM_ROOT)
