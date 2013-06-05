import os

from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import Device, DeviceMetadata, Zone


def get_host_name():
    name = ""
    try:
        name = eval("os.uname()[1]")
    except:
        try:
            name = eval("os.getenv('HOSTNAME', os.getenv('COMPUTERNAME') or '').lower()")
        except:
            name = ""
    return name


class Command(BaseCommand):
    args = "\"<name of device>\" \"<description of device>\""
    help = "Initialize device with optional name and description"

    def handle(self, *args, **options):
        if DeviceMetadata.objects.filter(is_own_device=True).count() > 0:
            self.stderr.write("Error: This device has already been initialized; aborting.\n")
            return
        if len(args) >= 1 and args[0]:
            name = args[0]
        else:
            name = get_host_name()
        if len(args) >= 2 and args[1]:
            description = args[1]
        else:
            description = ""
            
        Device.initialize_own_device(name=name, description=description)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))
        
        # Get all zones.  There should be zero or one.  If there is one,
        #   then create a sync session and call register, which will force
        #   an offline registration 
        all_zones = Zone.objects.get()
        if len(all_zones)>1:
            raise Exception("There should never be more than one zone in the database at this time!")
        if len(all_zones)==1:
            all_zone_certs = Zone.register_offline(Device, getattr(settings, "INSTALL_CERTIFICATES", []))
            