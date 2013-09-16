import os

from django.core.management.base import BaseCommand, CommandError

from securesync.models import Device, DeviceMetadata
from utils.general import get_host_name


class Command(BaseCommand):
    args = "\"<name of device>\" \"<description of device>\""
    help = "Initialize device with optional name and description"

    def handle(self, *args, **options):
        if DeviceMetadata.objects.filter(is_own_device=True).count() > 0:
            raise CommandError("Error: This device has already been initialized; aborting.\n")

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
