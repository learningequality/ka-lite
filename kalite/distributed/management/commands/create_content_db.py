from django.core.management.base import BaseCommand, CommandError
from django.conf import settings as django_settings
from kalite.topic_tools import settings
import os
import json
from sqlitedict import SqliteDict

logging = django_settings.LOG


class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.info("Converting...")

        convert(settings.CONTENT_FILEPATH, settings.CONTENT_CACHE_FILEPATH)


def convert(jsonfilepath, sqlitefilepath):
    with open(jsonfilepath) as f:
        items = json.load(f)

    with SqliteDict(sqlitefilepath) as kalitedict:
        kalitedict.update(items)
        kalitedict.commit()
