import sys

from django.utils import unittest

from securesync.models import *
from utils.testing.general import all_classes_in_module


@unittest.skipIf(sys.version_info < (2,7), "Test requires python version >= 2.7")
class UnicodeModelsTest(unittest.TestCase):
    korean_string = unichr(54392)

    def test_unicode_string(self):

        # Make sure we're testing all classes
        #   NOTE: we're not testing SyncedLog, nor SyncedModel
        found_classes = filter(lambda class_obj: "__unicode__" in dir(class_obj), all_classes_in_module("securesync.models"))
        known_classes = [Device, DeviceMetadata, DeviceZone, Facility, FacilityGroup, FacilityUser, RegisteredDevicePublicKey, SyncSession, SyncedLog, SyncedModel, Zone]
        self.assertTrue(not set(found_classes) - set(known_classes), "test for unknown classes in the module.")

        # Stand-alone classes
        dev = Device(name=self.korean_string)
        self.assertNotIn(unicode(dev), "Bad Unicode data", "Device: Bad conversion to unicode.")

        fac = Facility(name=self.korean_string)
        self.assertNotIn(unicode(fac), "Bad Unicode data", "Facility: Bad conversion to unicode.")

        fg = FacilityGroup(facility=fac, name=self.korean_string)
        self.assertNotIn(unicode(fg), "Bad Unicode data", "FacilityGroup: Bad conversion to unicode.")

        zon = Zone(name=self.korean_string)
        self.assertNotIn(unicode(zon), "Bad Unicode data", "Zone: Bad conversion to unicode.")

        # Classes using other classes
        fu = FacilityUser(
            facility=fac, 
            group=fg, 
            first_name=self.korean_string, 
            last_name=self.korean_string, 
            username=self.korean_string,
            notes=self.korean_string,
            password=self.korean_string,
        )
        self.assertNotIn(unicode(fu), "Bad Unicode data", "FacilityUser: Bad conversion to unicode.")

        syncsess = SyncSession(
            client_device=dev, 
            server_device=dev, 
            client_nonce=self.korean_string, 
            server_nonce=self.korean_string, 
            client_version=self.korean_string,
            client_os=self.korean_string,
        )
        self.assertNotIn(unicode(syncsess), "Bad Unicode data", "SyncSession: Bad conversion to unicode.")

        dz = DeviceZone(device=dev, zone=zon)
        self.assertNotIn(unicode(dz), "Bad Unicode data", "DeviceZone: Bad conversion to unicode.")

        pkey = RegisteredDevicePublicKey(zone=zon, public_key=self.korean_string)
        self.assertNotIn(unicode(pkey), "Bad Unicode data", "RegisteredDevicePublicKey: Bad conversion to unicode.")
