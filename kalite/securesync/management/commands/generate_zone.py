from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import Device, DeviceZone, Zone


class Command(BaseCommand):
    args = '<name of zone> <description of zone>'
    help = "Create zone with given name"

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("You shouldn't be trying to generate a zone on a central server instance!")
        elif Zone.objects.all().count() > 0:
            raise CommandError("This device already has a zone.")

        zone_name        = args[0] if len(args) >= 1 else "Device %s's self-generated zone" % Device.get_own_device().name
        zone_description = args[1] if (len(args) >= 2 and args[1]) else ""

        # Create some data
        self.stdout.write("Generating a zone.\n")
        zone = Zone(name=zone_name, description=zone_description)
        zone.sign()  # sign with local device
        zone.save()
        self.stdout.write("Done!\n")
