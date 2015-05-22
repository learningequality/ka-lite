import json
import os

from django.core.management.base import BaseCommand
from fle_utils.general import softload_json

from kalite import settings; logging = settings.LOG
from kalite.main.models import Content

# From topic_tools/__init__.py
CONTENT_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "contents.json")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        raw_items = softload_json(CONTENT_FILEPATH, logger=logging.debug, raises=False)
        for k, v in raw_items.iteritems():
            content, _ = Content.objects.get_or_create(id=k)
            content.blob = json.dumps(v)
            content.save()