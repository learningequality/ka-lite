import os

from django.core.management.base import BaseCommand, CommandError

import version
from securesync.models import Device, DeviceMetadata

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
        Device.initialize_own_device(name=name, description=description, version=version.VERSION)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))
        