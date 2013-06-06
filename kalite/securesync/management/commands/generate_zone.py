from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import Zone, ZoneInstallCertificate


class Command(BaseCommand):
    args = '"<name of zone>"'
    help = "Create zone with given name"

    def command_error(self, msg):
        self.stderr.write("Error: %s\n" % msg)
        exit(1)
        
    def handle(self, *args, **options):
        if settings.CENTRAL_SERVER:
            self.command_error("Error: you shouldn't be trying to generate a zone on a central server instance!")
        
        if Zone.objects.all().count() > 0:
            self.command_error("Error: This device already has a zone; aborting!\n")
            
        zone_name   = args[0] if (len(args) >= 1 and args[0]) else self.command_error("Must specify the zone name")
        
        # Create some data
        self.stdout.write("Generating a zone.\n")
        zone = Zone(name=zone_name)
        zone.save()
        self.stdout.write("Generating a zone installation certificate.\n")
        cert = ZoneInstallCertificate(zone=zone, raw_value="my local zone certificate")
        cert.save()

                        
