"""
"""
import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import unittest
from django.test.utils import override_settings

from .base import SecuresyncTestCase
from .decorators import distributed_server_test, central_server_test
from .. import VERSION
from ..models import Device, Zone, DeviceZone, ZoneInvitation, ChainOfTrust
from fle_utils.crypto import Key
from fle_utils.general import version_diff


class TestChainOfTrust(SecuresyncTestCase):
    def setUp(self):
        Device.own_device = None  # clear the cache, which isn't cleared across tests otherwise.
        super(SecuresyncTestCase, self).setUp()

    def tearDown(self):
        super(SecuresyncTestCase, self).tearDown()
        Device.own_device = None  # clear the cache, which isn't cleared across tests otherwise.

    @unittest.skipIf(version_diff("0.13", VERSION) > 0, "generate_zone not available before v0.13.")
    @distributed_server_test
    def test_valid_own_device(self):
        """
        Chain of trust:
        1. Zone created by this device
        2. Another device joins (no central server) through an invitation
        """
        own_device = Device.get_own_device()

        call_command("generate_zone")  # put own_device on a zone
        self.assertEqual(DeviceZone.objects.filter(device=own_device).count(), 1, "Own device should be on a zone after calling generate_zone.")
        zone = Zone.objects.all()[0]

        new_device = Device(name="new_device")  # make a new device
        new_device.set_key(Key())
        new_device.save()  # get an ID
        new_device.get_metadata().save()

        # Now create an invitation, and claim that invitation for the new device.
        invitation = ZoneInvitation.generate(zone=zone, invited_by=own_device)
        invitation.claim(used_by=new_device)
        self.assertEqual(invitation.used_by, new_device, "Invitation should now be used by device %s" % new_device)
        self.assertEqual(DeviceZone.objects.filter(device=new_device).count(), 1, "There should be a DeviceZone for device %s" % new_device)
        self.assertEqual(DeviceZone.objects.get(device=new_device).zone, zone, "DeviceZone for device %s should be zone %s" % (new_device, zone))

        # Now get a chain of trust establishing the new device on the zone
        chain = ChainOfTrust(zone=zone, device=new_device)
        self.assertTrue(chain.verify(), "Chain of trust should verify.")


    @central_server_test
    def test_valid_trusted(self):
        """
        Chain of trust:
        1. Zone created by this device
        2. Another device joins (no central server) through an invitation
        """
        own_device = Device.get_own_device()
        zone = Zone(name="test_zone")
        zone.save()

        new_device = Device(name="new_device")  # make a new device
        new_device.set_key(Key())
        new_device.save()  # get an ID
        new_device.get_metadata().save()

        # Now create an invitation, and claim that invitation for the new device.
        invitation = ZoneInvitation.generate(zone=zone, invited_by=own_device)
        invitation.claim(used_by=new_device)
        self.assertEqual(invitation.used_by, new_device, "Invitation should now be used by device %s" % new_device)
        self.assertEqual(DeviceZone.objects.filter(device=new_device).count(), 1, "There should be a DeviceZone for device %s" % new_device)
        self.assertEqual(DeviceZone.objects.get(device=new_device).zone, zone, "DeviceZone for device %s should be zone %s" % (new_device, zone))

        # Now get a chain of trust establishing the new device on the zone
        chain = ChainOfTrust(zone=zone, device=new_device)
        self.assertTrue(chain.verify(), "Chain of trust should verify.")

    @override_settings(DEBUG=True)
    @distributed_server_test
    @unittest.skipIf(version_diff("0.13", VERSION) > 0, "generate_zone not available before v0.13.")
    def test_invalid_invitation(self):
        """
        Chain of trust:
        1. Zone created by this device
        2. Another device joins (no central server) without an invitation--assert!
        """
        own_device = Device.get_own_device()

        call_command("generate_zone")  # put own_device on a zone
        zone = Zone.objects.all()[0]

        new_device = Device(name="new_device")  # make a new device
        new_device.set_key(Key())
        new_device.save()  # get an ID
        new_device.get_metadata().save()

        # Now create an illegal invitation--one that's not signed by the zone creator
        with self.assertRaises(ValidationError):
            ZoneInvitation.generate(zone=zone, invited_by=new_device)

        #
        invitation = ZoneInvitation(zone=zone, invited_by=new_device)
        with self.assertRaises(ValidationError):
            invitation.set_key(Key())
