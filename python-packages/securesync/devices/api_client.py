"""
"""
import json
import urllib

from django.core.urlresolvers import reverse

from .models import *
from ..engine.utils import serialize, deserialize
from ..api_client import BaseClient
from fle_utils.internet.functions import set_query_params

class RegistrationClient(BaseClient):
    """
    """
    def register(self, prove_self=False):
        """Register this device with a zone.  There are two methods:

        1.register_prove_self_registration:
            We joined a zone while offline, during install--either by
            using pre-packaged zone information, or generating our own
            zone.  In this case, we have to prove our permission to be
            on the zone.

        2. register_via_preregistered_key (deprecated):
            We have no zone information; instead, we connect with the
            central server directly, and get zone information from
            there.  This requires a previous manual step, where the
            public key of this device has been registered to be accepted
            onto that zone.
        """
        # Get the required model data by registering (online and offline options available)
        try:
#            if not prove_self:
            models = self.register_via_preregistered_key()
#            else:
#                (models,response) = self.register_prove_self_registration()

        except Exception as e:
            # Some of our exceptions are actually json blobs from the server.
            #   Try loading them to pass on that error info.
            try:
                return json.loads(e.args[0])
            except:
                return { "code": "unexpected_exception", "error": e.args[0] }

        # If we got here, we've successfully registered, and
        #   have the model data necessary for completing registration!
        for model in models:
            # BUG(bcipolli)
            # Shouldn't we care when things fail to verify??
            if not model.object.verify():
                logging.warn("\n\n\nFailed to verify model: %s!\n\n\n" % unicode(model.object))

            # save the imported model, and mark the returned Device as trusted
            if isinstance(model.object, Device):
                model.object.save(is_trusted=True, imported=True, increment_counters=False)
            else:
                model.object.save(imported=True, increment_counters=False)

        # If that all completes successfully, then we've registered!  Woot!
        return {"code": "registered"}


    def register_prove_self_registration(self):
        """
        Prove that we belong on our zone by providing the chain of trust,
        from us to the creator of the zone.
        """
        # Get all the
        own_device = Device.get_own_device()
        try:
            own_devicezone = DeviceZone.objects.get(device=own_device)  # We exit if not found
        except DeviceZone.DoesNotExist:
            # This should never actually happen--when upgrading to this new code,
            #   all devices should be on a zone.
            # However, if somehow that fails, let's try to create one now!
            raise Exception("Shared network not installed.  Try running the `generate_zone` command.")

        own_zone = own_devicezone.zone
        chain_of_trust = ChainOfTrust(device=own_device, zone=own_zone)

        # For now, just try with one certificate
        #
        # Serialize for any version; in the current implementation, we assume the central server has
        #   a version at least as new as ours, so can handle whatever data we send.
        #
        # the other side will have to reconstruct the chain from the object list
        object_list = [own_device] + chain_of_trust.objects()
        r = self.post("register", {
            "client_device": serialize(object_list, ensure_ascii=False),
        })

        # Failed to register with any certificate
        if r.status_code != 200:
            raise Exception(r.content)

        # When we register, we should receive the model information we require.
        #   Make sure to deserialize for our version.
        return (deserialize(r.content, dest_version=own_device.get_version()), r)


    def register_via_preregistered_key(self):
        """Register this device with a zone, through the central server directly"""

        own_device = Device.get_own_device()

        # Since we can't know the version of the remote device (yet),
        #   we give it everything we possibly can (don't specify a dest_version)
        #
        # Note that (currently) this should never fail--the central server (which we're sending
        #   these objects to) should always have a higher version.
        r = self.post("register", {
            "client_device": serialize([own_device], ensure_ascii=False),
        })

        # If they don't understand, our assumption is broken.
        # TODO BLOCKER 0.14 (rtibbles) update all our HTTP response codes to be properly semantic
        if (r.status_code == 500 or r.status_code == 400) and "Device has no field named 'version'" in r.content:
            raise Exception("Central server is of an older version than us?")

        # Failed to register with any certificate
        elif r.status_code != 200:
            raise Exception(r.content)

        else:
            # Save to our local store.  By NOT passing a src_version,
            #   we're saying it's OK to just store what we can.
            return deserialize(r.content, src_version=None, dest_version=own_device.get_version())

    def get_registration_url(self, **kwargs):

        if "device_key" not in kwargs:
            kwargs["device_key"] = urllib.quote(Device.get_own_device().public_key)

        return self.path_to_url(set_query_params(reverse("register_public_key"), kwargs))
