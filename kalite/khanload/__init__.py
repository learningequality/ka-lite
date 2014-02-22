import os

import settings


kind_slugs = {
    "Video": "v/",
    "Exercise": "e/",
    "Topic": ""
}
KHANLOAD_CACHE_DIR = os.path.join(settings.PROJECT_PATH, "../_khanload_cache")