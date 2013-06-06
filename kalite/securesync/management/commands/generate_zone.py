from django.core.management.base import BaseCommand, CommandError

import settings
from securesync.models import Zone, ZoneInstallCertificate


class Command(BaseCommand):
    args = '<name of zone> <description of zone>'
    help = "Create zone with given name"

    def command_error(self, msg):
        self.stderr.write("Error: %s\n" % msg)
        exit(1)
        
    def handle(self, *args, **options):
        #if settings.CENTRAL_SERVER:
        #    self.command_error("Error: you shouldn't be trying to generate a zone on a central server instance!")
        
        if Zone.objects.all().count() > 0:
            self.stderr.write("Warning: This device already has a zone; what are you up to?\n")
            
        zone_name   = args[0] if (len(args) >= 1 and args[0]) else self.command_error("Must specify the zone name")
        zone_description = args[1] if (len(args) >=2 and args[1]) else ""
        
        # Create some data
        self.stdout.write("Generating a zone.\n")
        zone = Zone(name=zone_name, description=zone_description)
        zone.save()
        self.stdout.write("Done!")
                        
