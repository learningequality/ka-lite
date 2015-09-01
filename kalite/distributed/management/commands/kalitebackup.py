import os
from optparse import make_option

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

from kalite.distributed import backup


try:
    os.makedirs(settings.BACKUP_DIRPATH)
except OSError:
    if not os.path.isdir(settings.BACKUP_DIRPATH):
        raise

class Command(BaseCommand):

    help = "Perform a backup."
    option_list = BaseCommand.option_list + (
        make_option(
            '--file',
            dest='BACKUP_DIRPATH',
            default=settings.BACKUP_DIRPATH,
            help="File path"),
        )

    def handle(self, *args, **options):
        try:
            call_command('dbbackup', filepath=settings.BACKUP_DIRPATH, database='default')
        except KeyError:
            pass
        backup.file_rename()