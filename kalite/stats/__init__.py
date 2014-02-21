import logging
import os

from django.conf import settings

from utils.general import ensure_dir


STATS_LOG_FILEPATH = os.path.join(settings.PROJECT_PATH, 'logs', 'stats.log')

# Note: beta level logger. Move to config file/dictionary format
def stats_logger(loggername="kalite.stats"):
    ensure_dir(os.path.dirname(STATS_LOG_FILEPATH))

    logger = logging.getLogger(loggername)
    logger.addHandler(_file_handler())

    return logger

def _file_handler():
    handler = logging.FileHandler(STATS_LOG_FILEPATH, encoding='utf-8', delay=True)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    return handler
