import os

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

import settings
import version
from securesync.models import Device, DeviceMetadata, Zone, ZoneInvitation
from shared import serializers
from utils.general import get_host_name


class Command(BaseCommand):
    args = "\"<name of device>\" \"<description of device>\""
    help = "Initialize device with optional name and description"

    install_json_file = os.path.join(settings.STATIC_ROOT, "data", "install_data.json")

    def handle(self, *args, **options):
        if DeviceMetadata.objects.filter(is_own_device=True).count() > 0:
            raise CommandError("Error: This device has already been initialized; aborting.\n")

        name        = args[0] if (len(args) >= 1 and args[0]) else get_host_name()
        description = args[1] if (len(args) >= 2 and args[1]) else ""
        data_file   = args[2] if (len(args) >= 3 and args[2]) else self.install_json_file

        # Validate parameters
        if not os.path.exists(data_file):
            raise CommandError("Could not find resource file %s; installation will run, but may have restricted syncing functionality." % data_file)

        Device.initialize_own_device(name=name, description=description)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))

        # Nothing to do with a central server
        if settings.CENTRAL_SERVER:
            return

        # Now we're definitely not central server, so ... go for it!
        # Import a zone (for machines sharing zones)
        try:
            Zone.load_zone_for_offline_install(in_file=data_file)
            self.stdout.write("Successfully imported zone information from %s\n" % data_file)
            os.remove(data_file)
        except Exception as e:
            raise CommandError("Error importing objects: %s\n" % str(e)) 

        # Generate a zone (for stand-alone machines)
        unused_invitations = ZoneInvitation.objects.filter(device=None).exclude(private_key=None)
        if unused_invitations:
            invitation = unused_invitations[0]
        else:
            invitation = None
            # Sorry dude, you weren't invited to the party.  You'll have to have your own!
            call_command("generate_zone")
            self.stdout.write("Successfully generated a stand-alone zone.\n") 


        # Grab the zone
        all_zones = Zone.objects.all()
        if len(all_zones) != 1:
            raise CommandError("There should always be exactly one zone in the database at this time!\n")
        zone = all_zones[0]

        # "Register" locally, offline
        try:
            Device.get_own_device().register_offline(zone=zone, invitation=invitation)
            self.stdout.write("Successfully registered (offline) to zone %s, using invitation '%s'\n" % (zone.name, invitation))
        except Exception as e:
            raise CommandError("Error completing offline registration: %s\n" % str(e))
