"""
"""
import os

from django.conf import settings


kind_slugs = {
    "Video": "v/",
    "Exercise": "e/",
    "Topic": "",
    "AssessmentItem": ""
}

KHANLOAD_CACHE_DIR = os.path.join(settings.PROJECT_PATH, "../_contentload_cache")