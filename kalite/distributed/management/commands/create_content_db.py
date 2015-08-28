from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json
from sqlitedict import SqliteDict

logging = settings.LOG


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
