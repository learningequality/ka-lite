"""
This is a command-line tool to execute functions helpful to testing.
"""

from optparse import make_option

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from config.models import Settings
from settings import LOG as logging
from securesync.models import Device, DeviceZone, Zone, Facility


#@distributed_server_only 
def unregister_distributed_server():
    """
    All local steps necessary for unregistering a server with a central server.
    
    Note that the remote steps (central-server-side) are NOT done.
      * Login as Django admin, go to admin page, select "devices", find your device and delete.
    """
    if settings.CENTRAL_SERVER:
        raise CommandError("'Unregister' does not make sense for a central server.  Aborting!")

    own_device = Device.get_own_device()
    
    # Delete zone info
    DeviceZone.objects.filter(device=own_device).delete()
    Zone.objects.all().delete()

    # Delete registered info
    Settings.delete("registered")  # setting to False doesn't work.

    # Delete central server
    Device.objects.filter(devicemetadata__is_trusted=True).delete()

def clean_db(interactive=False):
    """
    Delete kalite data associated with Zone, Facility and Device
    Does not remove the django admin accounts etc.
    """

    # Prompt for confirmation, if interactive
    if interactive and "yes" != raw_input(("WARNING: clean_db will permanently delete data!\nType 'yes' to continue, or 'no' to cancel: ")).lower():
        logging.info("Aborting command.")
        return

    logging.info("Cleaning Zone")
    Zone.objects.all().delete()
    logging.info("Cleaning Facility")
    Facility.objects.all().delete()
    logging.info("Cleaning Device")
    Device.objects.all().delete()


class Command(BaseCommand):
    help = "KA Lite test help"
    option_list = BaseCommand.option_list + (
    make_option('--noinput', action='store_false', dest='interactive', default=True,
            help='Tells Django to NOT prompt the user for input of any kind.'),)

    def handle(self, *args, **options):
        
        if not args:
            raise CommandError("Must specify a test-only method to run..")

        elif args[0] == "unregister":
            unregister_distributed_server()
            
        elif args[0] == "clean_db":
            clean_db(interactive=options["interactive"])

        else:
            raise CommandError("Unrecognized test-only method: %s" % args[0])
