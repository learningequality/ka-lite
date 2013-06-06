import os

from django.core.management.base import BaseCommand, CommandError

import kalite
import settings
from securesync.models import Device, DeviceMetadata, Zone
from securesync.utils import load_zone_for_offline_install
from kalite.utils.django_utils import call_command_with_output            

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
            exit(1)
            
        name        = args[0] if (len(args) >= 1 and args[0]) else get_host_name()
        description = args[1] if (len(args) >= 2 and args[1]) else ""
        obj_file    = args[2] if (len(args) >= 3 and args[2]) else None

        # Validate params
        if obj_file and not os.path.exists(obj_file):
            self.stderr.write("Could not find specified object file: %s" % obj_file)
            exit(1)

        # Create the device            
        Device.initialize_own_device(name=name, description=description, version=kalite.VERSION)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))
        
        # Get ready to import a zone
        if settings.CENTRAL_SERVER:
            if obj_file:
                self.stderr.write("Error: should not specify any zone information when installing a central server!")
                exit(1)
            else:
                exit(0) # done.
                
        # Now we're definitely not central server, so ... go for it!
        # Import a zone (for machines sharing zones)
        if obj_file:
            try:
                load_zone_for_offline_install(in_file=obj_file)
                self.stdout.write("Successfully imported zone information from %s\n" % obj_file)
            except Exception as e:
                self.stderr.write("Error importing objects: %s\n" % str(e)) 
                exit(1)       
        # Generate a zone (for stand-alone machines)
        else:
            out = call_command_with_output("generate_zone", "default zone")
            if not out[1]:
                self.stdout.write("Successfully generated a stand-alone zone.\n") 
            else:
                self.stderr.write("Error generating new zone: %s\n" % out[1])
                exit(1)
                          
        # Try to do offline install
        all_zones = Zone.objects.all()
        if len(all_zones)!=1:
            self.stderr.write("There should always be exactly one zone in the database at this time!\n")
            exit(1)
            
        try:
            zone = all_zones[0]
            cert = zone.register_offline(device = Device.get_own_device())
            if cert:
                self.stdout.write("Successfully registered (offline) to zone %s, using certificate '%s'\n" % (zone.name, cert))
                if obj_file and os.path.exists(obj_file):
                    os.remove(obj_file)
            else:
                self.stderr.write("Failed to register (offline) to zone %s; bad data in file? (%s)\n" % (zone.name, obj_file))
                exit(1)
        except Exception as e:
            self.stderr.write("Error completing offline registration: %s\n" % str(e))
            exit(1)
                    
