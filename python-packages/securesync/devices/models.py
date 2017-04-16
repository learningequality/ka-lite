"""
"""
import datetime
import logging
import uuid
from annoying.functions import get_object_or_None

from django.conf import settings
from django.contrib.auth.models import check_password
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models, transaction, IntegrityError
from django.db.models import Q
from django.db.models.expressions import F
from django.utils.text import compress_string
from django.utils.translation import ugettext_lazy as _

from .. import ID_MAX_LENGTH, IP_MAX_LENGTH, VERSION
from .. import crypto
from ..engine.models import SyncedModel, SyncedModelManager
from fle_utils.general import get_host_name
from fle_utils.django_utils.debugging import validate_via_booleans
from fle_utils.django_utils.classes import ExtendedModel


class RegisteredDevicePublicKey(ExtendedModel):
    public_key = models.CharField(max_length=500, help_text="(This field will be filled in automatically)")
    zone = models.ForeignKey("Zone")
    created_timestamp = models.DateTimeField(auto_now_add=True, null=True, default=None)  # Null for oldies
    used_timestamp = models.DateTimeField(null=True, default=None)

    class Meta:
        app_label = "securesync"

    def __unicode__(self):
        out_str = u"%s... (Zone: %s)" % (self.public_key[0:5], self.zone)
        out_str += (u"; created on %s" % self.created_timestamp) if self.created_timestamp else ""
        out_str += (u"; used on %s" % self.used_timestamp) if self.used_timestamp else ""
        return out_str

    def use(self):
        # Never should get called if timestamp
        assert not self.used_timestamp, "Cannot reuse public key registrations"
        self.used_timestamp = datetime.datetime.now()
        self.save()

    def is_used(self):
        return self.used_timestamp is not None


class UnregisteredDevice(ExtendedModel):
    """
    Bare list of all unregistered devices that 'ping' us with a device ID
    """
    id = models.CharField(primary_key=True, max_length=ID_MAX_LENGTH, editable=False)


class UnregisteredDevicePing(ExtendedModel):
    """
    Whenever we receive a session request from an unregistered device,
    we increase our counter
    """
    device = models.ForeignKey("UnregisteredDevice", unique=True)
    npings = models.IntegerField(default=0)
    last_ip = models.CharField(max_length=IP_MAX_LENGTH, blank=True)
    last_ping = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u"%s: %s pings, last on %s from %s" % (self.device.id, self.npings, self.last_ping, self.last_ip)

    @classmethod
    def record_ping(cls, id, ip):
        """
        We received a failed request to create a session; record that 'ping' in our DB
        """
        try:
            # Create the log (if necessary), update, and save
            # TODO: make a base class (in django_utils) that has get_or_initialize, and use that
            #   to shorten things here
            (cur_device, _) = UnregisteredDevice.objects.get_or_create(id=id)
            (cur_log, _) = cls.get_or_initialize(device=cur_device)  # get is safe, because device is unique

            cur_log.npings += 1
            cur_log.last_ip = ip
            cur_log.save()

        except Exception as e:
            # Never block functionality
            logging.error("Error recording unregistered device ping: %s" % e)


class DeviceMetadata(ExtendedModel):
    device = models.OneToOneField("Device", blank=True, null=True)
    is_trusted = models.BooleanField(default=False)
    is_own_device = models.BooleanField(default=False)
    is_demo_device = models.BooleanField(default=False)
    counter_position = models.IntegerField(default=0)

    class Meta:
        verbose_name_plural = "Device metadata"
        app_label = "securesync"

    def __unicode__(self):
        return u"(Device: %s)" % (self.device)


class Zone(SyncedModel):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        app_label = "securesync"

    #@central_server_only  # causes circular loop, to include here
    def get_org(self):
        """
        Reverse lookup of organization containing this zone.
        """
        orgs = self.organization_set.all()
        assert orgs.count() <= 1, "Zone must be contained by 0 or 1 organization(s)."

        return orgs[0] if orgs else None

    def is_member(self, device):
        """
        """
        try:
            return ChainOfTrust(zone=self, device=device).verify()
        except:
            return False

    @validate_via_booleans
    def validate(self):
        """
        Nothing to verify--ANYBODY can make a zone.  The question is
        if you can convince anybody else to join it :P
        """
        return True

    @classmethod
    def get_headless_zones(cls):
        """
        Method for getting all zones that aren't connected to at least one organization.
        """
        # Must import inline (not in header) to avoid import loop
        return Zone.objects.filter(organization=None)

    def __unicode__(self):
        return self.name


class DeviceZone(SyncedModel):
    device = models.ForeignKey("Device", unique=True)
    zone = models.ForeignKey("Zone", db_index=True)
    revoked = models.BooleanField(default=False)
    max_counter = models.IntegerField(blank=True, null=True)

    class Meta:
        app_label = "securesync"

    @validate_via_booleans
    def validate(self):
        """
        Verify that it was created by a trusted server (old-school),
        or that it has an invitation backing the devicezone (new-school)
        """
        if self.signed_by.is_trusted():
            return True
        invitation =  get_object_or_None(ZoneInvitation, used_by=self.device, zone=self.zone)
        return self.device == self.signed_by and invitation and invitation.verify()

    def __unicode__(self):
        return u"Device: %s, assigned to Zone: %s" % (self.device, self.zone)


class DeviceManager(SyncedModelManager):

    class Meta:
        app_label = "securesync"

    def by_zone(self, zone):
        # get Devices that belong to a particular zone, or are a trusted authority
        return self.by_zones([zone.id])

    def by_zones(self, zones):
        # get Devices that belong to a list of zone IDs, or are a trusted authority
        return self.filter(Q(devicezone__zone__id__in=zones, devicezone__revoked=False) |
            Q(devicemetadata__is_trusted=True))


class Device(SyncedModel):
    name = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)
    public_key = models.CharField(max_length=500, db_index=True)
    version = models.CharField(max_length=len("10.10.100"), default="0.9.2", blank=True); version.minversion="0.9.3"  # default comes from knowing when this feature was implemented!

    objects = DeviceManager()
    all_objects = DeviceManager(show_deleted=True)

    key = None
    own_device = None  # cached property, shared globally.

    class Meta:
        app_label = "securesync"

    def set_key(self, key):
        assert isinstance(key, crypto.Key), "key must be a crypto Key object"
        self.public_key = key.get_public_key_string()
        self.key = key

    def get_key(self):
        if not self.key:
            try:
                if self.get_metadata().is_own_device:
                    self.key = crypto.get_own_key()
            except Device.DoesNotExist:
                # get_metadata can fail if the Device instance hasn't been persisted to the db
                pass
            if not self.key and self.public_key:
                self.key = crypto.Key(public_key_string=self.public_key)
        return self.key

    def _hashable_representation(self):
        fields = ["signed_version", "name", "description", "public_key"]
        return super(Device, self)._hashable_representation(fields=fields)

    def get_metadata(self):
        try:
            return DeviceMetadata.objects.get_or_create(device=self)[0]
        except IntegrityError as e:
            # Possible from get_or_create if the DeviceMetadata object doesn't exist
            # and the Device hasn't been persisted to the database yet.
            raise Device.DoesNotExist()

    def get_counter_position(self):
        """
        """
        if not self.id:
            return 0

        else:
            return self.get_metadata().counter_position

    def set_counter_position(self, counter_position, soft_set=False):
        metadata = self.get_metadata()
        if not metadata.device.id:  # only happens if device has not been saved yet.  Should be changed to self.id
            return

        # It's often convenient to reset the position ONLY if the new counter position
        #   is higher than the old.  So, let people be lazy--but need to send in a flag,
        #   so it's clear that something a bit unusual is happening in a "set"
        if soft_set and self.signed_by.get_counter_position() >= counter_position:
            return

        assert counter_position >= metadata.counter_position, "You should not be setting the counter position to a number lower than its current value!"
        metadata.counter_position = counter_position
        metadata.save()

    @transaction.commit_on_success
    def increment_counter_position(self):
        """Increment and return the counter position for this device.
        TODO-BLOCKER(jamalex): While from testing, this new version seems much less prone to race conditions,
        it still seems like a possibility. Further testing would be good.
        """
        metadata = self.get_metadata()
        metadata.counter_position = F("counter_position") + 1
        metadata.save()
        return self.get_metadata().counter_position

    def full_clean(self, *args, **kwargs):
        # TODO(jamalex): we skip out here, because otherwise self-signed devices will fail
        pass

    def get_version(self):
        """
        Get this property through an accessor function,
        so that we can guarantee that the DB-stored version
        matches the hard-coded software version.
        """
        own_device = Device.get_own_device()
        if self == own_device and self.version != VERSION:
            self.version = VERSION
            self.save()
        return self.version

    @classmethod
    def get_default_version(cls):
        """Accessor method to probe the default version of a device (or field)"""
        return cls._meta.get_field("version").default

    @classmethod
    def get_own_device(cls):
        if not cls.own_device:
            devices = DeviceMetadata.objects.filter(is_own_device=True)
            if devices.count() == 0:
                cls.own_device = cls.initialize_own_device() # why don't we need name or description here?
            else:
                cls.own_device = devices[0].device
        return cls.own_device

    @classmethod
    def initialize_own_device(cls, **kwargs):
        """
        Create a device object for the installed device.  Part of installation.
        """
        kwargs["version"] = kwargs.get("version", VERSION)
        kwargs["name"] = kwargs.get("name", get_host_name())
        own_device = cls(**kwargs)
        own_device.set_key(crypto.get_own_key())

        # imported=True is for when the local device should not sign the object,
        #   and when counters should not be incremented.  That's our situation here!
        own_device.sign(device=own_device)  # must sign, in order to use imported codepath
        super(Device, own_device).save(imported=True, increment_counters=False)

        metadata = own_device.get_metadata()
        metadata.is_own_device = True
        metadata.is_trusted = settings.CENTRAL_SERVER  # this is OK to set, as DeviceMetata is NEVER synced.
        metadata.save()

        return own_device

    def __unicode__(self):
        return self.name or self.id[0:5]

    def get_zone(self):
        zones = self.devicezone_set.filter(revoked=False)
        return zones and zones[0].zone or None
    get_zone.short_description = "Zone"

    @validate_via_booleans
    def validate(self):
        if self.signed_by_id != self.id and not self.signed_by.get_metadata().is_trusted:
            raise ValidationError("Device is not self-signed.")
        return True

    def verify(self):
        if not self.validate():
            return False
        return self.get_key().verify(self._hashable_representation(), self.signature)

    def save(self, is_trusted=False, *args, **kwargs):
        # TODO(jamalex): uncomment out the following, but allow for devices created on old versions somehow
        # if self.id and self.id != self.get_uuid():
        #     raise ValidationError("ID must match device's public key.")
        if self.signed_by_id and self.signed_by_id != self.id and not self.signed_by.get_metadata().is_trusted:
            raise ValidationError("Devices must either be self-signed or signed by a trusted authority.")

        super(Device, self).save(*args, **kwargs)

        if is_trusted:
            metadata = self.get_metadata()
            metadata.is_trusted = True
            metadata.save()

    def get_uuid(self):
        """
        Device's UUID is dependent only on its public key.
        """
        assert self.public_key is not None, "public_key required for get_uuid"
        return uuid.uuid5(settings.ROOT_UUID_NAMESPACE, str(self.public_key)).hex

    @classmethod
    def get_central_server(cls):
        if settings.CENTRAL_SERVER:
            return Device.get_own_device()
        else:
            devices = Device.objects.filter(devicemetadata__is_trusted=True)
            return devices[0] if devices else None  # none if old computer, hasn't registered.

    def is_creator(self, model):
        return self == model.signed_by

    def is_trusted(self):
        return self.get_metadata().is_trusted

    def is_own_device(self):
        return self.get_metadata().is_own_device

    def is_registered(self):
        return self.get_zone() is not None


class ZoneInvitation(SyncedModel):
    """
    Public/private keypair, with the public key signed by
    the inviting party.
    """
    zone = models.ForeignKey("Zone")
    invited_by = models.ForeignKey("Device", related_name="+")
    used_by = models.ForeignKey("Device", blank=True, null=True, related_name="+")
    public_key = models.CharField(max_length=500)
    public_key_signature = models.CharField(max_length=500)
    private_key = models.CharField(max_length=2500, blank=True, null=True)
    revoked = models.BooleanField(default=False)

    key = None

    def __unicode__(self):
        outstr = u"Invitation for zone %s, invited by %s" % (self.zone.name, self.invited_by.name)
        if self.used_by:
            outstr += u", used by %s" % self.used_by.name
        if self.revoked:
            outstr += u" (REVOKED)"
        return outstr

    def _hashable_representation(self):
        fields = ["zone", "public_key", "public_key_signature"]
        return super(ZoneInvitation, self)._hashable_representation(fields=fields)

    def get_uuid(self):
        """
        ZoneInvitation's UUID is dependent only on its public key.
        """
        assert self.public_key is not None, "public_key required for get_uuid"
        return uuid.uuid5(settings.ROOT_UUID_NAMESPACE, str(self.public_key)).hex

    def set_key(self, key, invited_by=None):
        assert isinstance(key, crypto.Key), "key must be a crypto Key object"
        self.key = key
        self.public_key = key.get_public_key_string()
        self.private_key = key.get_private_key_string()

        self.invited_by = invited_by or self.invited_by
        assert self.invited_by, "must set invited_by, or pass in as parameter."
        assert self.invited_by.get_key(), "inviting Device must have a valid key."
        assert self.invited_by.get_key().get_private_key_string(), "inviting Device must have a valid key for signing."

        self.public_key_signature = self.invited_by.get_key().sign(self.public_key)
        if not self.verify():
            logging.debug("Created invalid ZoneInvitation.")

    def get_key(self):
        if not self.key:
            self.key = crypto.Key(public_key_string=self.public_key, private_key_string=self.private_key)
        return self.key

    @validate_via_booleans
    def validate(self):
        """
        Check that this Invitation is set up properly.
        """
        if not self.public_key_signature:
            raise ValidationError("Public key signature does not exist")
        elif not self.invited_by:
            raise ValidationError("Public key signee does not exist")
        elif not self.is_authorized(self.invited_by):
            raise ValidationError("Public key signee is on a different zone than this invitation, did not create the zone, and is not trusted.")
        elif self.revoked:
            raise ValidationError("ZoneInvitation was revoked.")
        return True

    def verify(self):
        if not self.validate():
            return False
        return self.invited_by.get_key().verify(self.public_key, self.public_key_signature)

    def claim(self, used_by):
        """
        Use this certificate to put Device used_by on this zone.
        """
        if self.used_by:
            raise Exception("This ZoneInvitation has already been used.")
        elif not self.private_key:
            raise Exception("Can only use a zone invitation with a private key.")
        elif ZoneInvitation.objects.filter(used_by=used_by).count():
            raise Exception("Device %s has already used %s zone invitation(s)." % (used_by, ZoneInvitation.objects.filter(used_by=used_by).count()))

        self.used_by = used_by
        self.save()

        # Create the device zone.  As the zone owner, self-signing is OK!
        logging.debug("Successfully claimed the zone invitation, generating a DeviceZone")
        devicezone = DeviceZone(device=used_by, zone=self.zone)
        devicezone.save()  # sign this ourselves--we authorize this claim

    def is_authorized(self, device=None):
        """
        Authorized to be in the chain / generate Invitations
        """
        is_auth = False
        is_auth = is_auth or self.zone.signed_by == device
        is_auth = is_auth or self.zone == device.get_zone()
        is_auth = is_auth or device.is_trusted()
        return is_auth


    @classmethod
    def generate(cls, zone=None, invited_by=None):
        """
        Returns an unsaved object.
        """
        invited_by = invited_by or Device.get_own_device()
        zone = zone or invited_by.get_zone()
        assert zone and invited_by

        invitation = ZoneInvitation(zone=zone, invited_by=invited_by)
        invitation.set_key(crypto.Key())
        invitation.verify()

        return invitation


class ChainOfTrust(object):
    """
    Object for computing and validating a chain of signatures
    linking a device to a zone through a set of ZoneInvitations or DeviceZones.

    Note: This currently subclasses object, but a version subclassing Model
    could act as a ChainOfTrust cache, so that _compute would not need
    to be called every time, but instead only when a Model didn't exist in the
    database.
    """
    MAX_CHAIN_LENGTH = 100

    def __init__(self, zone=None, device=None):
        """
        Represents a chain of trust, establishing membership of a device on a zone.

        Output
        """
        self.device = device or Device.get_own_device()
        self.zone = zone or Device.get_own_device().get_zone()
        self.zone_owner = zone.signed_by
        self.chain = self._compute()

    def objects(self):
        """
        Return a list of objects without their relationships,
        as well as supporting objects (such as DeviceMetadata)
        """
        device_list = [dict["device"] for dict in self.chain]
        device_list += [self.zone_owner]  # make sure the zone owner makes it on there!

        invitation_list = [dict["zone_invitation"] for dict in self.chain if dict["zone_invitation"]]
        invitation_list += ZoneInvitation.objects.filter(used_by=self.zone_owner)

        devicezone_list = [dict["device_zone"] for dict in self.chain if dict["device_zone"]]
        devicezone_list += DeviceZone.objects.filter(device=self.zone_owner)

        # We return in this order because we know this order is necessary for serializing
        #   objects (due to interdependencies)
        return device_list + [self.zone] + invitation_list + devicezone_list

    @validate_via_booleans
    def validate(self):
        if not self.device:
            raise ValidationError("Origin device is not set.")
        if not self.zone:
            raise ValidationError("Target zone is not set.")
        if not self.zone_owner:
            raise ValidationError("Owner of zone is not set.")
        if not self.chain:
            raise ValidationError("Chain was not yet computed.")

        if self.device != self.chain[0]["device"]:
            raise ValidationError("Origin device is not the first link in the chain.")
        if self.zone_owner != self.chain[-1]["device"] and not self.chain[-1]["device"].is_trusted():
            raise ValidationError("Terminal device is not the zone owner or a trusted device.")

        return True

    def verify(self):
        """
        This only works for models in the database,
        so all models in the chain must be saved to the DB first
        (in a transaction), then backed out if they don't verify.
        """
        if not self.validate():
            return False

        # Make sure they're all on the same zone
        prev_invitation = None
        for link in self.chain:
            device = link["device"]
            invitation = link["zone_invitation"]
            devicezone = link["device_zone"]

            if not device.is_trusted() and device.get_zone() != self.zone:
                # Every link in the chain must be trusted or (verified) on the zone.
                # This requires that all models already be in the database.
                return False

            if invitation:
                if not invitation.is_authorized(device):
                    # Device was not authorized to be on the zone / use this invitation
                    return False
                if prev_invitation and not device.get_key().verify(prev_invitation.public_key, prev_invitation.public_key_signature):
                    # The previous invitation should be signed by the next device in the chain.
                    return False

            if devicezone:
                if devicezone.zone != self.zone:
                    # DeviceZone is for another zone.
                    #   Note: Shouldn't ever be--since we checked the device's zone above,
                    #   and it gets its info from the DeviceZone... but let's be safe.
                    return False

            prev_invitation = invitation
        return True

    def _compute(self):
        """
        Track from one DeviceZone to whomever originally signed the zone
        (the zone creator--either the central server, or a device)

        Returns an (ordered) list of dictionaries (Device, DeviceZone), defining the chain of trust.
        """
        return self.__class__.compute_one_way(zone=self.zone, from_device=self.device, to_device=self.zone_owner)

    @classmethod
    def compute_one_way(cls, zone, from_device, to_device):
        """
        """
        assert from_device.is_trusted() or from_device.get_zone() == zone
        # Trace back from this device to the zone-trusted device.
        chain = [{"device": from_device}]
        devices_in_chain = set([])

        for i in range(cls.MAX_CHAIN_LENGTH):  # max chain size: 1000 (avoids infinite loops)
            # We're going to traverse the chain backwards, until we get to
            #   the zone_owner (to_device), or a trusted device.
            cur_link = chain[-1]

            # Get a devicezone and/or zone invitation for the current device.
            cur_link["zone_invitation"] = get_object_or_None(ZoneInvitation, used_by=cur_link["device"].signed_by, revoked=False)
            if cur_link["zone_invitation"]:
                cur_link["zone_invitation"].verify()  # make sure it's a valid invitation
            cur_link["device_zone"] = get_object_or_None(DeviceZone, device=cur_link["device"].signed_by, revoked=False)

            # Determine the next step.  Three terminal steps, one continuing step
            if not cur_link["zone_invitation"] and not cur_link["device_zone"]:
                # A break in the chain.  No connection between the device and the zone.
                break
            elif cur_link["device"] == to_device or cur_link["device"].is_trusted():
                logging.debug("Found end of chain!")
                break;
            next_device = getattr(cur_link["zone_invitation"], "invited_by", None)
            next_device = next_device or getattr(cur_link["device_zone"], "signed_by")
            if next_device in devices_in_chain:
                logging.warn("loop detected.")
                break
            else:
                # So far, we're OK--keep looking for the (valid) end of the chain
                assert next_device.is_trusted() or next_device.get_zone() == zone
                devices_in_chain.add(next_device)
                chain.append({"device": next_device})

        # Validate the chain of trust to the zone zone_owner
        terminal_link = chain[-1]
        terminal_device = terminal_link["device"]
        obj = terminal_link["zone_invitation"] or terminal_link["device_zone"]
        if obj and not (terminal_device.is_creator(obj) or terminal_device.is_trusted()):
            logging.warn("Could not verify chain of trust.")
        return chain
