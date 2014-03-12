import logging
import os

from django.conf import settings

from utils.general import ensure_dir


STATS_LOG_DIRPATH = os.path.join(settings.DATA_PATH, 'logs')

# Note: beta level logger. Move to config file/dictionary format
def stats_logger(loggertype="stats", loggername=None):
    """Return a logger that will log to a file"""

    loggername = loggername or "kalite." + loggertype

    logger = logging.getLogger(loggername)
    if not logger.handlers:
        # For now, limit 1 handler per logger.
        logger.addHandler(_file_handler(loggername=loggername))

    return logger


def _file_handler(filename=None, loggername=None):
    """Return a file handler with a filename specific to the logging type"""

    filename = filename or (loggername + ".log" if loggername else "stats.log")

    # Make sure that the path exists for logging to GO!
    ensure_dir(STATS_LOG_DIRPATH)
    logger_filepath = os.path.join(STATS_LOG_DIRPATH, filename)

    handler = logging.FileHandler(logger_filepath, encoding='utf-8', delay=True)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))

    return handler
