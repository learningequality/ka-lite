from kalite.utils.testing import create_test_admin, KALiteEcosystemTestCase

class CrossLocalServerSyncTestCase(KALiteEcosystemTestCase):
    
    def setUp(self, *args, **kwargs):
        return super(CrossLocalServerSyncTestCase, self).setUp(*args, **kwargs)
        
    def test_one(self):
        create_test_admin()
        import pdb; pdb.set_trace()
    
#    def test_setup(self):
#        import pdb; pdb.set_trace()
    
