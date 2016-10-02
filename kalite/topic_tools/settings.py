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

# Where runtime data is stored
CONTENT_DATABASE_PATH = os.path.join(settings.DEFAULT_DATABASE_DIR, "content_{channel}_{language}.sqlite")

# Where db templates are stored
CONTENT_DATABASE_TEMPLATE_PATH = os.path.join(settings.DB_CONTENT_ITEM_TEMPLATE_DIR, "content_{channel}_{language}.sqlite")

CHANNEL = getattr(settings, "CHANNEL", "khan")

KHAN_EXERCISES_DIRPATH = os.path.join(settings.STATIC_ROOT, "js", "distributed", "perseus", "ke")

TOPIC_RECOMMENDATION_DEPTH = 3
