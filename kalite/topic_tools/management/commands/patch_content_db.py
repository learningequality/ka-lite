
from django.conf import settings as django_settings
from kalite.topic_tools.settings import CONTENT_DATABASE_TEMPLATE_PATH, \
    CONTENT_DATABASE_PATH
from optparse import make_option
logging = django_settings.LOG

from playhouse import migrate
from peewee import BooleanField, SqliteDatabase

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option("--template",
                    action="store_true",
                    dest="template",
                    default=False,
                    help="Patch a template"),
    )

    def handle(self, *args, **kwargs):

        template = kwargs.get('template', False)

        if template:
            db = SqliteDatabase(CONTENT_DATABASE_TEMPLATE_PATH.format(channel="khan", language="en"))
        else:
            db = SqliteDatabase(CONTENT_DATABASE_PATH.format(channel="khan", language="en"))

        schedule_download = BooleanField(default=False)
        migrator = migrate.SqliteMigrator(db)
        migrate.migrate(
            migrator.add_column('item', 'schedule_download', schedule_download),
        )
