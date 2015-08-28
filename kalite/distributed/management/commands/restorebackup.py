import os
import sys

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

from optparse import make_option


class Command(BaseCommand):
    help = "Restore backup to a previous state."
    option_list = BaseCommand.option_list + (
        make_option(
            '--file',
            dest='backup_filepath',
            default="",
            help="File path"),
        )

    def handle(self, *args, **options):
        backup_filepath = options['backup_filepath']
        if(options['backup_filepath']):
            if(os.path.isfile(backup_filepath)):
                call_command('dbrestore', filepath=backup_filepath, database='default') #perform restore from the given filepath
            else:
                print 'The given file was not found.'
                sys.exit(1)
        else:
            file_list = os.listdir(settings.BACKUP_DIRPATH) #Retrieve the filenames present in the BACKUP_DIRPATH
            filelist = []
            for i, f in enumerate(file_list):
                print i, f.replace(".backup", "")
                filelist.append(f)
            if filelist:
                print "Please enter a file-number to restore:"
                backup_option = int(raw_input())
                try:
                    restoref = filelist[backup_option] #file to be restored based on x
                    backup_filepath = os.path.join(settings.BACKUP_DIRPATH, restoref) #create file path
                    call_command('dbrestore', filepath=backup_filepath, database='default') #perform restore
                except IndexError:
                    print 'Number option out of bounds.'
                    sys.exit(1)
            else:
                print 'No files available to restore.'
                sys.exit(1)