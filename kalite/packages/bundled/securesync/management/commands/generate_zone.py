"""
"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import Device, DeviceZone, Zone, ZoneInvitation


class Command(BaseCommand):
    args = '<name of sharing network> <description of sharing network>'
    help = "Create sharing network with given name"

    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            raise CommandError("You shouldn't be trying to put the central server on a sharing network!")

        own_device = Device.get_own_device()
        if DeviceZone.objects.filter(device=own_device).count() > 0:
            raise CommandError("This device already belongs to a sharing network.")

        zone_name        = args[0] if len(args) >= 1 else "Sharing network for Device %s" % own_device.name
        zone_description = args[1] if (len(args) >= 2 and args[1]) else ""

        # Create the zone
        self.stdout.write("Generating a sharing network.\n")
        zone = Zone(name=zone_name, description=zone_description)
        zone.save()  # this will sign the zone with the current device

        # Create the zone invitation--you're invited to a party of one!
        self.stdout.write("Generating a sharing network invitation--from me, to me!\n")
        invitation = ZoneInvitation.generate(zone=zone, invited_by=own_device)
        invitation.save()
        invitation.claim(used_by=own_device)
        self.stdout.write("Done!\n")
