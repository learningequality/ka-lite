import os

from django.core.management.base import BaseCommand
from fle_utils.general import softload_json

from kalite import settings; logging = settings.LOG
from kalite.main.models import AssessmentItem

# From topic_tools/__init__.py
ASSESSMENT_ITEMS_FILEPATH = os.path.join(settings.CHANNEL_DATA_PATH, "assessmentitems.json")


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        raw_items = softload_json(ASSESSMENT_ITEMS_FILEPATH, logger=logging.debug, raises=False)
        for k, v in raw_items.iteritems():
            ai, _ = AssessmentItem.objects.get_or_create(id=k)
            ai.item_data = v['item_data']
            ai.author_names = v['author_names']
            ai.save()