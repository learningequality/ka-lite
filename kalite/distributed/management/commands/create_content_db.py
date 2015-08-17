from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json
from sqlitedict import SqliteDict

logging = settings.LOG
EXERCISES_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "exercises.json")
EXERCISES_SQLITEPATH = os.path.join(
    settings.CHANNEL_DATA_PATH, "exercises.sqlite")
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")
CONTENT_SQLITEPATH = os.path.join(
    settings.CHANNEL_DATA_PATH, "contents.sqlite")


class Command(BaseCommand):

    def handle(self, *args, **options):
        logging.info("Converting...")

        convert(CONTENT_FILEPATH, CONTENT_SQLITEPATH)


def convert(jsonfilepath, sqlitefilepath):
    with open(jsonfilepath) as f:
        items = json.load(f)

    with SqliteDict(sqlitefilepath) as kalitedict:
        kalitedict.update(items)
        kalitedict.commit()
