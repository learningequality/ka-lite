from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import Device, DeviceZone, Zone, ZoneInvitation


class Command(BaseCommand):
    args = '<name of zone> <description of zone>'
    help = "Create zone with given name"

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("You shouldn't be trying to generate a zone on a central server instance!")

        own_device = Device.get_own_device()
        if DeviceZone.objects.filter(device=own_device).count() > 0:
            raise CommandError("This device is already on a zone.")

        zone_name        = args[0] if len(args) >= 1 else "Self-generated zone for Device %s" % own_device.name
        zone_description = args[1] if (len(args) >= 2 and args[1]) else ""

        # Create the zone
        self.stdout.write("Generating a zone.\n")
        zone = Zone(name=zone_name, description=zone_description)
        zone.sign()  # sign with local device
        zone.save()

        # Create the zone invitation--you're invited to a party of one!
        self.stdout.write("Generating a zone invitation--from me, to me!\n")
        invitation = ZoneInvitation.generate(zone=zone, invited_by=own_device)
        invitation.save()
        invitation.claim(used_by=own_device)
        self.stdout.write("Done!\n")
