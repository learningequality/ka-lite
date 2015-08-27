import os

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connections
from fle_utils.general import softload_json
from optparse import make_option

from django.conf import settings as django_settings
logging = django_settings.LOG

from kalite.topic_tools.models import AssessmentItem

from kalite.contentload import settings


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("-a", "--assessment-items-filepath",
                    action="store",
                    dest="assessment_items_filepath",
                    default=settings.KHAN_ASSESSMENT_ITEM_JSON_PATH,
                    help="Override the JSON data source to import assessment items from"),
        make_option("-d", "--database-path",
                    action="store",
                    dest="database_path",
                    default="",
                    help="Override the destination path for the assessment item DB file"),
        make_option("-b", "--bulk-create",
                    action="store_true",
                    dest="bulk_create",
                    default=False,
                    help="Create the records in bulk (warning: will delete destination DB first)"),
    )

    def handle(self, assessment_items_filepath, database_path, bulk_create, *args, **kwargs):

        database_alias = "assessment_items"

        # temporarily swap out the database path for the desired target
        database_path = database_path or connections.databases[database_alias]['NAME']
        temp_db_path, connections.databases[database_alias]['NAME'] = connections.databases[database_alias]['NAME'], database_path

        if bulk_create and os.path.isfile(database_path):
            os.remove(database_path)

        call_command("syncdb", interactive=False, database=database_alias)

        raw_items = softload_json(assessment_items_filepath, logger=logging.debug, raises=False)
        if bulk_create:
            items = [AssessmentItem(id=k, item_data=v["item_data"], author_names=v["author_names"]) for k, v in raw_items.items()]
            AssessmentItem.objects.bulk_create(items)
        else:
            for k, v in raw_items.iteritems():
                AssessmentItem.objects.using(database_alias).get_or_create(id=k, defaults={"item_data": v["item_data"], "author_names": v["author_names"]})

        # revert the database path to the original path
        connections.databases[database_alias]['NAME'] = temp_db_path