"""
This is a command-line tool to execute functions helpful to testing.
"""
from django.core.management.base import BaseCommand, CommandError

import settings
from config.models import Settings
from securesync.models import Device, DeviceZone, Zone
#from utils.decorators import distributed_server_only


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


class Command(BaseCommand):
    help = "KA Lite test help"

    def handle(self, *args, **options):
        if not args:
            raise CommandError("Must specify a test-only method to run..")

        elif args[0] == "unregister":
            unregister_distributed_server()

        else:
            raise CommandError("Unrecognized test-only method: %s" % args[0])


