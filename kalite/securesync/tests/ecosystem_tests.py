import copy
import os
import platform
import shutil
import tempfile

from kalite import settings
from kalite.utils.django_utils import call_command_with_output
from kalite.utils.testing.base import create_test_admin
from playground.test_tools.mount_branch import KaLiteServer, KaLiteSelfZipProject


class KALiteEcosystemTestCase(KALiteTestCase):
    """A testcase involving an "ecosystem" of KA Lite servers: 1 central server and two distributed servers
    on the same zone.
    
    Subclasses could look at more complex scenarios."""
    
    # TODO(bcipolli) move setup and teardown code to class (not instance);
    #   not sure how to tear down in this case, though...............
        
    def __init__(self, *args, **kwargs):
        self.log = settings.LOG
        self.zip_file = tempfile.mkstemp()[1]
        self.base_dir = tempfile.mkdtemp()
                
        return super(KALiteEcosystemTestCase, self).__init__(*args, **kwargs)

    def setup_ports(self):        
        self.port = int(self.live_server_url.split(":")[2])

        assert os.environ.get("DJANGO_LIVE_TEST_SERVER_ADDRESS",""), "This testcase can only be run running under the liveserver django test option.  For KA Lite, this should be set up by our TestRunner (which is set up in settings.py)"
        self.open_ports = [int(p) for p in os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'].split(":")[1].split("-")]
        if len(self.open_ports) != 2:
            raise Exception("Unable to parse ports. Use a simple range (8000-8080)")
        self.open_ports = set(range(self.open_ports[0], self.open_ports[1]+1)) - {self.port,}


    def setUp(self, *args, **kwargs):
        """Package two servers just like this one, and mount."""
        
        self.setup_ports()

        # Make sure the setup is 2 local, 1 central
        # First is for this server, 2 and 3 are for the others
        server_types = ["central" if settings.CENTRAL_SERVER else "local", 'local' if settings.CENTRAL_SERVER else 'central', 'local2']

        self.log.info("Setting up ecosystem: your server [%s; port %d], plus %s servers" % (server_types[0], self.port, str(server_types[1:])))


        # Create a zip file 
        self.log.info("Creating zip package for your server; please wait.")
        out = call_command_with_output("package_for_download", platform=platform.system(), locale='en', file=self.zip_file)
        self.log.info("Completed zip package for your server.")
        
        # Copy, install, and start the servers
        self.log.info("Installing two servers; please wait.")
        kap = KaLiteSelfZipProject(base_dir=self.base_dir, zip_file=self.zip_file, persistent_ports=False)
        kap.mount_project(server_types=server_types[1:], host="127.0.0.1", open_ports=self.open_ports, port_map={server_types[0]: self.port})

        # Save all servers to be accessible
        own_server = KaLiteServer(base_dir=settings.PROJECT_PATH+"/../", server_type=server_types[0], port=self.port, central_server_host="127.0.0.1", central_server_port = kap.port_map['central'])
        self.servers = copy.copy(kap.servers)
        self.servers[server_types[0]] = own_server
        
        return super(KALiteEcosystemTestCase, self).setUp(*args, **kwargs)
        
    
    def tearDown(self):
        self.log.info("Tearing down ecosystem test servers")
        shutil.rmtree(self.base_dir)
        os.remove(self.zip_file)

class CrossLocalServerSyncTestCase(KALiteEcosystemTestCase):
    
    def setUp(self, *args, **kwargs):
        return super(CrossLocalServerSyncTestCase, self).setUp(*args, **kwargs)

    def call_command(self, server, command, params_string="", expect_success=True):
        out = self.servers[server].call_command(command=command, params_string=params_string)
        if expect_success:
            self.assertEqual(out['exit_code'], 0, "Check exit code.")
            self.assertEqual(out['stderr'], None, "Check stderr")
            return out['stdout']
        else:
            return out
        
    def shell_plus(self, server, commands, expect_success=True):
        out = self.servers[server].shell_plus(commands=commands)
        if expect_success:
            self.assertIn('exit_code', out.keys(), "Check exit code.")
            self.assertEqual(out['exit_code'], 0, "Check exit code.")
            self.assertEqual(out['stderr'], None, "Check stderr")
            return out['stdout']
        else:
            return out
            
    def test_one(self):
        create_test_admin()

#        self.servers['central']
#        self.servers['local']
#        self.servers['local2']
        
        # Generate data
        self.call_command("local2", "generatefakedata")
        
        n_elogs = int(self.shell_plus("local2", "ExerciseLog.objects.all().count()"))
        n_vlogs = int(self.shell_plus("local2", "VideoLog.objects.all().count()"))
    
        out = self.call_command("local2", "syncmodels")
        out = self.call_command("local", "syncmodels")
            
        import pdb; pdb.set_trace()
#        n_elogs = int(self.shell_plus("central", "ExerciseLog.objects.all().count()"))

