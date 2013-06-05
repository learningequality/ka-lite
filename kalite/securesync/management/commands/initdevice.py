import os

from django.core.management.base import BaseCommand, CommandError

import kalite
import settings
from securesync.models import Device, DeviceMetadata, Zone
from securesync.utils import load_zone_for_offline_install
            

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
            return
            
        name        = args[0] if (len(args) >= 1 and args[0]) else get_host_name()
        description = args[1] if (len(args) >= 2 and args[1]) else ""
        obj_file    = args[2] if (len(args) >= 3 and args[2]) else None

        # Validate params
        if obj_file and not os.path.exists(obj_file):
            self.stderr.write("Could not find specified object file: %s" % obj_file)
            return 1

        # Create the device            
        Device.initialize_own_device(name=name, description=description, version=kalite.VERSION)
        self.stdout.write("Device '%s'%s has been successfully initialized.\n"
            % (name, description and (" ('%s')" % description) or ""))
        
        # Import data
        if obj_file:
            try:
                load_zone_for_offline_install(in_file=obj_file)
            except Exception as e:
                self.stderr.write("Error importing objects: %s\n" % str(e)) 
                return 1       
        
        # Try to do offline install
        all_zones = Zone.objects.all()
        if len(all_zones)>1:
            self.stderr.write("There should never be more than one zone in the database at this time!\n")
            return 1
            
        elif len(all_zones)==1:
            try:
                zone = all_zones[0]
                cert = zone.register_offline(device = Device.get_own_device())
                if cert:
                    self.stdout.write("Successfully registered (offline) to zone %s, using certificate %s\n" % (zone.name, cert))
                else:
                    self.stderr.write("Failed to register (offline) to zone %s\n" % zone.name)
            except Exception as e:
                self.stderr.write("Error completing offline registration: %s\n" % str(e))
                return 1
                        
