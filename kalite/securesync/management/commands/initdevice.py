import os
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction

import settings
import version
from securesync.models import Device, DeviceMetadata, Zone, ZoneInvitation
from securesync.views import set_as_registered
from settings import LOG as logging
from shared import serializers
from utils.general import get_host_name


@transaction.commit_on_success  # because the objects may not be in order, do in a single transaction
def load_data_for_offline_install(in_file):
    """
    Receives a serialized file for import.
    Import the file--nothing more!
    
    File should contain:
    * Central server object
    and, optionally
    * Zone object
    * Device and DeviceZone / ZoneInvitation objects (chain of trust)

    Essentially duplicates code from securesync.device.api_client:RegistrationClient
    """
    assert os.path.exists(in_file), "in_file must exist."
    with open(in_file, "r") as fp:
        models = serializers.deserialize("versioned-json", fp.read())  # all must be in a consistent version
    
    # First object should be the central server.
    try:
        central_server = models.next().object
    except Exception as e:
        logging.debug("Exception loading central server object: %s" % e)
        return
    logging.debug("Saving object %s" % central_server)
    assert isinstance(central_server, Device)
    central_server.save(imported=True, is_trusted=True)

    # Everything else, import as is.
    for model in models:
        logging.debug("Saving object %s" % model.object)
        model.object.save(imported=True)


class Command(BaseCommand):
    args = "\"<name of device>\" \"<description of device>\""
    help = "Initialize device with optional name and description"

    install_json_filename = "install_data.json"
    install_json_file = os.path.join(settings.STATIC_ROOT, "data", install_json_filename)

    def handle(self, *args, **options):
        if DeviceMetadata.objects.filter(is_own_device=True).count() > 0:
            raise CommandError("Error: This device has already been initialized; aborting.\n")

        name        = args[0] if (len(args) >= 1 and args[0]) else get_host_name()
        description = args[1] if (len(args) >= 2 and args[1]) else ""
        data_file   = args[2] if (len(args) >= 3 and args[2]) else self.install_json_file

        own_device = Device.initialize_own_device(name=name, description=description)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))

        # Nothing to do with a central server
        if settings.CENTRAL_SERVER:
            return

        # Now we're definitely not central server, so ... go for it!
        # Import a zone (for machines sharing zones)
        if not os.path.exists(data_file):
            sys.stderr.write("Could not find resource file %s.  This may cause warnings to appear when updating your KA Lite version." % data_file)
        else:
            try:
                load_data_for_offline_install(in_file=data_file)
                self.stdout.write("Successfully imported offline data from %s\n" % data_file)
                if not settings.DEBUG:
                    os.remove(data_file)
            except Exception as e:
                raise CommandError("Error importing offline data from %s: %s\n" % (data_file, str(e))) 

        # Join a zone, either by grabbing an open invitation, or by generating one.
        unused_invitations = ZoneInvitation.objects.filter(used_by=None).exclude(private_key=None)
        if unused_invitations:
            # Zone info existed in the data blob we received.  Use it to join the zone!
            invitation = unused_invitations[0]
            invitation.claim(used_by=own_device)
            self.stdout.write("Successfully joined existing zone %s, using invitation %s.\n" % (invitation.zone, invitation))

        else:
            # Sorry dude, you weren't invited to the party.  You'll have to have your own!
            # Generate a zone (for stand-alone machines)
            call_command("generate_zone")
            self.stdout.write("Successfully generated a stand-alone zone, and joined!.\n") 

        set_as_registered()  # would try to sync