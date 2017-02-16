import os
import shutil
import sys

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear out all usage data (NOT including videos and content packs)"

    option_list = BaseCommand.option_list + (
        make_option('--noinput',
            action='store_true',
            dest='noinput',
            default=False,
            help='Do not warn, just clear out user data',
        ),
    )

    def handle(self, *args, **options):
        
        if not options['noinput']:
            
            print (
                "This will remove all usage data and device registration "
                "permanently."
            )
            yn = raw_input("Are you sure? [y/n] ")
            if yn.lower().strip() != "y":
                print "No problem, have a nice day!"
                sys.exit(0)
        
        shutil.copy(
            settings.DB_TEMPLATE_DEFAULT,
            settings.DEFAULT_DATABASE_PATH
        )

        if os.path.exists(settings.SECRET_KEY_FILE):
            os.unlink(settings.SECRET_KEY_FILE)
        
        print ""
        print "Successfully cleared out database and secret device key."
        print ""
        print (
            "This device will automatically be re-initialized upon next "
            "kalite start-up."
        )
        print ""
        print "KA Lite installation is ready to be cloned to other devices."
