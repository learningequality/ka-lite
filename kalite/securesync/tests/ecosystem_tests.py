import copy
import os
import platform
import requests
import shutil
import tempfile

from kalite import settings
from playground.test_tools.mount_branch import KaLiteServer, KaLiteSelfZipProject
from securesync.models import Device, DeviceZone, Zone
from utils.django_utils import call_command_with_output
from utils.testing.base import create_test_admin, KALiteTestCase


class KALiteEcosystemTestCase(KALiteTestCase):
    """
    A utility class for implmementing testcases involving an "ecosystem" of KA Lite servers:
    1 central server and two distributed servers, on the same zone.
    
    Subclasses could look at complex syncing scenarios, using the setup provided here.
    """
    
    # TODO(bcipolli) move setup and teardown code to class (not instance);
    #   not sure how to tear down in this case, though...............
        
    def __init__(self, *args, **kwargs):
        self.log = settings.LOG
        self.zip_file = tempfile.mkstemp()[1]
        self.temp_dir = tempfile.mkdtemp()
        self.zone_name = kwargs.get("zone_name", "Syncing test zone")
        
        return super(KALiteEcosystemTestCase, self).__init__(*args, **kwargs)


    def setup_ports(self):        
        """Get the live server port (self), plus three more ports (remotes)"""
        self.port = int(self.live_server_url.split(":")[2])

        assert os.environ.get("DJANGO_LIVE_TEST_SERVER_ADDRESS",""), "This testcase can only be run running under the liveserver django test option.  For KA Lite, this should be set up by our TestRunner (which is set up in settings.py)"
        
        # Parse the open ports
        self.open_ports = [int(p) for p in os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'].split(":")[1].split("-")]
        if len(self.open_ports) != 2:
            raise Exception("Unable to parse ports. Use a simple range (8000-8080). Used: '%s'" % os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'])
            
        # Choose some (but not one that's used for this liveserver)
        self.open_ports = set(range(self.open_ports[0], self.open_ports[1]+2)) - {self.port,}


    def setUp(self, *args, **kwargs):
        """Package two servers just like this one, and mount.
        
        One major issue here is the interaction of the TEST liveserver,
        which installs its own database, and the database of the (offline)
        non-test server, which is accessed on every call that goes directly
        to the filesystem or OS.
        
        In order to deal with this, we currently set up THREE servers
        into temp directories, and don't use the current server at all.
        """

        self.log.info("Setting up ecosystem")

        self.setup_ports()
        server_types = ["central", "local", "local2"]
        port_map = dict(zip(server_types, self.open_ports))  # this works as wished, due to niceties of zip

        # Create a zip file package FROM THIS CODEBASE
        self.log.info("Creating zip package from your server; please wait.")
        out = call_command_with_output("package_for_download", server_type="central", platform=platform.system(), locale='en', file=self.zip_file)
        
        # Install the central server
        self.log.info("Installing the central server; please wait.")
        kap = KaLiteSelfZipProject(base_dir=self.temp_dir, zip_file=self.zip_file, persistent_ports=False)
        kap.mount_project(server_types=["central"], host="127.0.0.1", port_map=port_map)
        self.servers = copy.copy(kap.servers)

        # Create a zone
        out = self.shell_plus("central", "Zone(name='%s').save()" % self.zone_name)
        zone_id = eval(self.shell_plus("central", "Zone.objects.all()[0].id"))
        
        # Create a zip file package from the central codebase.
        self.log.info("Creating zip package from installed central server; please wait.")
        from utils.packaging import package_offline_install_zip
        zoned_zip_file = self.shell_plus("central", "import utils.packaging\nutils.packaging.package_offline_install_zip(platform='%s', locale='en', zone=Zone.objects.all()[0], num_certificates=2, central_server='http://127.0.0.1:%d')" % (platform.system(), port_map["central"]))
        zoned_zip_file = eval(zoned_zip_file[5:]) # prune cruft

        # Install the other two servers
        ncservers = set(server_types)-{"central",}
        self.log.info("Installing the other servers (%s); please wait." % ncservers)
        kap = KaLiteSelfZipProject(base_dir=self.temp_dir, zip_file=zoned_zip_file, persistent_ports=False)
        kap.mount_project(server_types=ncservers, host="127.0.0.1", port_map=port_map)
        for server in ncservers:
            self.servers[server] = kap.servers[server]

        # Now start all the servers
        for server in self.servers.values():
            server.start_server()
            
        return super(KALiteEcosystemTestCase, self).setUp(*args, **kwargs)


    def tearDown(self):
        self.log.info("Tearing down ecosystem test servers")
        shutil.rmtree(self.temp_dir)
        os.remove(self.zip_file)


    def call_command(self, server, command, params_string="", expect_success=True):
        """Utility function for calling out to call_command, then repackaging the output."""
        out = self.servers[server].call_command(command=command, params_string=params_string)
        if expect_success:
            self.assertEqual(out['exit_code'], 0, "Check exit code.")
            self.assertEqual(out['stderr'], None, "Check stderr")
            return out['stdout']
        else:
            return out
        
    def shell_plus(self, server, commands, expect_success=True):
        """Utility function for calling out to shell_plus, then repackaging the output."""
        out = self.servers[server].shell_plus(commands=commands)
        if expect_success:
            self.assertIn('exit_code', out.keys(), "Check exit code.")
            self.assertEqual(out['exit_code'], 0, "Check exit code.")
            self.assertEqual(out['stderr'], None, "Check stderr")
            return out['stdout']
        else:
            return out

            
class CrossLocalServerSyncTestCase(KALiteEcosystemTestCase):
    """Basic sync test case."""
    
    def check_has_logs(self, server, log_type, count):
        """Check that given server has the number of logs expected, for the given type."""

        val = self.shell_plus(server, "%s.objects.all().count()" % log_type)
        self.assertEqual(count, int(val), "Checking that %s has %d %s logs." % (server, count, log_type))

    
    def check_has_device(self, server, device):
        """Check that device, zone, and devicezone data exist for the given device on the given server."""

        # Get the device and zone information
        device_id = eval(self.shell_plus(device, "Device.objects.filter(devicemetadata__is_own_device=True)[0].id"))
        zone_id = eval(self.shell_plus(device, "DeviceZone.objects.filter(device='%s')[0].zone.id" % device_id))

        # double eval is a bug to track down ... sometime.                
        self.assertEqual(device, eval(eval(self.shell_plus(server, "Device.objects.get(id='%s').name" % device_id))), "Device %s exists on %s" % (device, server))
        self.assertEqual(self.zone_name, eval(self.shell_plus(server, "Device.objects.get(id='%s').get_zone().name" % device_id)), "Zone for %s exists on %s" % (device, server))


    def test_one(self):
        ## Generate data on local2
        out = self.call_command("local2", "generatefakedata")
        n_elogs = int(self.shell_plus("local2", "ExerciseLog.objects.all().count()"))
        n_vlogs = int(self.shell_plus("local2", "VideoLog.objects.all().count()"))
        self.assertTrue(n_elogs > 0, "local2 has more than 0 exercise logs, after running 'generatefakedata'")

        ## Sync local2 to the central server            
        out = self.call_command("local2", "syncmodels")
        self.assertIn("Total errors: 0", out)
        
        # Validate data on central server
        self.check_has_logs(server="central", log_type="ExerciseLog", count=n_elogs)
        self.check_has_logs(server="central", log_type="VideoLog", count=n_vlogs)
        self.check_has_device(server="central", device="local2")
        
        # Validate no data on local
        self.check_has_logs(server="local", log_type="ExerciseLog", count=0)
        self.check_has_logs(server="local", log_type="VideoLog", count=0)


        ## Sync local to the central server (should get local2 data)
        out = self.call_command("local", "syncmodels")
        self.assertIn("Total errors: 0", out)
        
        # Validate data on local
        self.check_has_logs(server="local", log_type="ExerciseLog", count=n_elogs)
        self.check_has_logs(server="local", log_type="VideoLog", count=n_vlogs)
        self.check_has_device(server="local", device="local2")
        

        ## Last one: sync local2 to the central server (should get local device)
        out = self.call_command("local2", "syncmodels")
        self.assertIn("Total errors: 0", out)
        
        # Validate data on local2
        self.check_has_logs(server="local", log_type="ExerciseLog", count=n_elogs)
        self.check_has_logs(server="local", log_type="VideoLog", count=n_vlogs)
        self.check_has_device(server="local2", device="local")

        import pdb; pdb.set_trace()
