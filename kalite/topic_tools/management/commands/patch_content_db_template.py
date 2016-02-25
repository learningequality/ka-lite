
from django.conf import settings as django_settings
from kalite.topic_tools.settings import CONTENT_DATABASE_TEMPLATE_PATH
logging = django_settings.LOG

from playhouse import migrate
from peewee import BooleanField, SqliteDatabase

from django.core.management.base import BaseCommand


class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        db = SqliteDatabase(CONTENT_DATABASE_TEMPLATE_PATH.format(channel="khan", language="en"))
        schedule_download = BooleanField(default=False)
        migrator = migrate.SqliteMigrator(db)
        migrate.migrate(
            migrator.add_column('item', 'schedule_download', schedule_download),
        )
