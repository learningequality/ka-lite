"""
"""
import logging
import os
import sys
from annoying.functions import get_object_or_None

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ...engine.utils import deserialize
from ...models import Device, DeviceMetadata, DeviceZone, ZoneInvitation
from ...views import initialize_registration
from fle_utils.general import get_host_name


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
        models = deserialize(fp.read())  # all must be in a consistent version

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
    invitation = None
    for model in models:
        try:
            logging.debug("Saving object %s" % model.object)
            model.object.save(imported=True)

            if isinstance(model.object, ZoneInvitation):
                # Zone info existed in the data blob we received.  Use it to join the zone!
                invitation = model.object
                if invitation.used_by is None:
                    invitation.claim(used_by=Device.get_own_device())
        except ValidationError as e:
            # Happens when there's duplication of data, sometimes.
            #   Shouldn't happen, but keeping this here to make things
            #   a bit more robust.
            logging.error("Failed to import model %s" % model)

    return invitation


def confirm_or_generate_zone(invitation=None, device_zone=None):

    invitation = invitation or get_object_or_None(ZoneInvitation, used_by=Device.get_own_device())
    device_zone = device_zone or get_object_or_None(DeviceZone, device=Device.get_own_device())
    if invitation:
        sys.stdout.write("Confirmed existing sharing network %s, using invitation %s.\n" % (invitation.zone, invitation))
    elif device_zone:
        sys.stdout.write("Confirmed existing sharing network %s, using device_zone %s.\n" % (device_zone.zone, device_zone))

    else:
        # Sorry dude, you weren't invited to the party.  You'll have to have your own!
        # Generate a zone (for stand-alone machines)
        call_command("generate_zone")
        sys.stdout.write("Successfully generated a sharing network, and joined!.\n")

    initialize_registration()  # would try to sync


class Command(BaseCommand):
    args = "\"<name of device>\" \"<description of device>\""
    help = "Initialize device with optional name and description"

    data_json_filename = "network_data.json"
    data_json_file = os.path.join(settings.STATIC_ROOT, "data", data_json_filename)

    def handle(self, *args, **options):
        if DeviceMetadata.objects.filter(is_own_device=True).count() > 0:
            raise CommandError("Error: This device has already been initialized; aborting.\n")

        name        = args[0] if (len(args) >= 1 and args[0]) else get_host_name()
        description = args[1] if (len(args) >= 2 and args[1]) else ""
        data_file   = args[2] if (len(args) >= 3 and args[2]) else self.data_json_file

        own_device = Device.initialize_own_device(name=name, description=description)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))

        # Nothing to do with a central server
        if settings.CENTRAL_SERVER:
            return
        elif True:  # for 0.10.3, short-cut to avoid invitation logic.
            return

        # Now we're definitely not central server, so ... go for it!
        # Import a zone (for machines sharing zones), and join if it works!
        invitation = None
        if not os.path.exists(data_file):
            sys.stderr.write("Could not find resource file %s.  This may cause warnings to appear when updating your KA Lite version.\n" % data_file)
        else:
            try:
                invitation = load_data_for_offline_install(in_file=data_file)
                self.stdout.write("Successfully imported offline data from %s\n" % data_file)

                # Doesn't hurt to keep data around.
                #if not settings.DEBUG:
                #    os.remove(data_file)
            except Exception as e:
                raise CommandError("Error importing offline data from %s: %s\n" % (data_file, e))

        confirm_or_generate_zone(invitation)
