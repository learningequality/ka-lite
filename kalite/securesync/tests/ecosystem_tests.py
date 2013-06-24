from kalite.utils.testing import create_test_admin, KALiteEcosystemTestCase

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

