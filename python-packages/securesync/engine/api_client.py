"""
"""
import re
import json


from .utils import get_serialized_models, save_serialized_models, get_device_counters, deserialize
from .models import *
from ..api_client import BaseClient
from ..devices.api_client import RegistrationClient
from ..devices.models import *
from fle_utils.platforms import get_os_name


class SyncClient(BaseClient):
    """ This is for the distributed server, for establishing a client session with
    the central server.  Over that session, syncing can occur in multiple requests.

    Note that in the future, this object may be used to sync
    between two distributed servers (i.e. peer-to-peer sync)!"""
    session = None

    def post(self, path, payload={}, *args, **kwargs):
        if self.session and self.session.client_nonce:
            payload["client_nonce"] = self.session.client_nonce
        return super(SyncClient, self).post(path, payload, *args, **kwargs)

    def get(self, path, payload={}, *args, **kwargs):
        if self.session and self.session.client_nonce:
            payload["client_nonce"] = self.session.client_nonce
        # add a random parameter to ensure the request is not cached
        return super(SyncClient, self).get(path, payload, *args, **kwargs)

    def start_session(self):
        """A 'session' to exchange data"""

        if self.verbose:
            print "\nCLIENT: start_session"

        if self.session:
            self.close_session()
        self.session = SyncSession()

        if self.verbose:
            print "CLIENT: start_session, request #1"

        # Request one: validate me as a sessionable partner
        (self.session.client_nonce,
         self.session.client_device,
         data) = self.validate_me_on_server()

        # Able to create session
        signature = data.get("signature", "")

        # Once again, we assume that (currently) the central server's version is >= ours,
        #   We just store what we can.
        own_device = self.session.client_device
        session = deserialize(data["session"], src_version=None, dest_version=own_device.get_version()).next().object
        self.session.server_nonce = session.server_nonce
        self.session.server_device = session.server_device
        if not session.verify_server_signature(signature):
            raise Exception("Sever session signature did not match.")
        if session.client_nonce != self.session.client_nonce:
            raise Exception("Client session nonce did not match.")
        if session.client_device != self.session.client_device:
            raise Exception("Client session device did not match.")
        if self.require_trusted and not session.server_device.is_trusted():
            raise Exception("The server is not trusted, don't make a session with THAT.")
        self.session.verified = True
        self.session.timestamp = session.timestamp

        self.session.ip = self.parsed_url.netloc

        self.session.save()

        if self.verbose:
            print "CLIENT: start_session, request #2"

        # Request two: create your own session, and
        #   report the result back to me for validation
        r = self.post("session/create", {
            "client_nonce": self.session.client_nonce,
            "client_device": self.session.client_device.pk,
            "server_nonce": self.session.server_nonce,
            "server_device": self.session.server_device.pk,
            "signature": self.session.sign(),
        })

        if r.status_code == 200:
            return "success"
        else:
            return r


    def validate_me_on_server(self, recursive_retry=False):
        client_nonce = uuid.uuid4().hex
        client_device = Device.get_own_device()

        r = self.post("session/create", {
            "client_nonce": client_nonce,
            "client_device": client_device.pk,
            "client_version": client_device.get_version(),
            "client_os": get_os_name(),
        })
        raw_data = r.content
        try:
            data = json.loads(raw_data)
        except ValueError as e:
            z = re.search(r'exception_value">([^<]+)<', unicode(raw_data), re.MULTILINE)
            if z:
                raise Exception("Could not load JSON\n; server error=%s" % z.group(1))
            else:
                raise Exception("Could not load JSON\n; raw content=%s" % raw_data)

        # Happens if the server reports an error
        if data.get("error"):
            # This happens when a device points to a new central server,
            #   either because it changed, or because it self-registered.
            if not recursive_retry and "Client device matching id could not be found." in data["error"]:
                resp = RegistrationClient().register(prove_self=True)
                if resp.get("error"):
                    raise Exception("Error [code=%s]: %s" % (resp.get("code",""), resp.get("error","")))
                elif resp.get("code") != "registered":
                    raise Exception("Unexpected code: '%s'" % resp.get("code",""))
                # We seem to have succeeded registering through prove_self;
                #   let's try to validate again (but without retrying again, lest we loop forever!)
                return self.validate_me_on_server(recursive_retry=True)
            raise Exception(data.get("error", ""))

        return (client_nonce, client_device, data)


    def close_session(self):

        if self.verbose:
            print "\nCLIENT: close_session"

        if not self.session:
            return
        self.post("session/destroy", {
            "client_nonce": self.session.client_nonce
        })
        self.session = None
        return "success"

    def get_server_device_counters(self):
        r = self.get("device/counters")
        data = json.loads(r.content or "{}")
        if "error" in data:
            raise Exception("Server error in retrieving counters: " + data["error"])
        return data.get("device_counters", {})

    def get_client_device_counters(self):
        return get_device_counters(zone=self.session.client_device.get_zone())

    def sync_device_records(self):

        if self.verbose:
            print "\nCLIENT: sync_device_records"

        server_counters = self.get_server_device_counters()
        client_counters = self.get_client_device_counters()

        if self.verbose:
            print client_counters, server_counters
            print "COUNTERS: ([D]istributed, [C]entral)"
            for device in set(server_counters.keys()).union(client_counters.keys()):
                print "\t", device[0:5], "D%d" % client_counters.get(device, 0), "C%d" % server_counters.get(device, 0)

        devices_to_download = []
        devices_to_upload = []

        counters_to_download = {}
        counters_to_upload = {}

        # loop through the devices we have locally
        for device_id in client_counters:
            if device_id not in server_counters:
                devices_to_upload.append(device_id)
                counters_to_upload[device_id] = 0
            elif client_counters[device_id] > server_counters[device_id]:
                counters_to_upload[device_id] = server_counters[device_id]

        # loop through the devices the server has told us about
        for device_id in server_counters:
            if device_id not in client_counters:
                devices_to_download.append(device_id)
                counters_to_download[device_id] = 0
            elif server_counters[device_id] > client_counters[device_id]:
                counters_to_download[device_id] = client_counters[device_id]

        if self.verbose:
            print "CLIENT: devices_to_upload = %r" % devices_to_upload
            print "CLIENT: devices_to_download = %r" % devices_to_download

        response = json.loads(self.post("device/download", {"devices": devices_to_download}).content)
        # As usual, we're deserializing from the central server, so we assume that what we're getting
        #   is "smartly" dumbed down for us.  We don't need to specify the src_version, as it's
        #   pre-cleaned for us.

        download_results = save_serialized_models(response.get("devices", "[]"), increment_counters=False, verbose=self.verbose)

        # BUGFIX(bcipolli) metadata only gets created if models are
        #   streamed; if a device is downloaded but no models are downloaded,
        #   metadata does not exist.  Let's just force it here.
        for device_id in devices_to_download: # force
            try:
                d = Device.all_objects.get(id=device_id)  # even do deleted devices.
            except Exception as e:
                logging.error("Exception locating device %s for metadata creation: %s" % (device_id, e))
                continue

            if not d.get_counter_position():  # this would be nonzero if the device sync'd models
                d.set_counter_position(counters_to_download[device_id])

        self.session.models_downloaded += download_results["saved_model_count"]
        self.display_and_count_errors(download_results, context_name="downloading devices")

        self.session.save()

        # TODO(jamalex): upload local devices as well? only needed once we have P2P syncing

        return (counters_to_download, counters_to_upload)

    def display_and_count_errors(self, data, context_name="syncing data"):

        if "error" in data:
            print "Server error(s) in %s: %s" % (context_name, data["error"])
            self.session.errors += 1

        if "exceptions" in data:
            print "Server exceptions(s) in %s: %s" % (context_name, data["exceptions"])
            self.session.errors += 1

    def sync_models(self):
        """
        This method first syncs device counters and device objects, so that the two computers
        can determine who has what and, in comparison, what it needs to request.

        Then, it uses those device records to partially download and partially upload.
        Not all at once--that would be less robust!

        Afterwards, it returns summary statistics about what was synced, but no specific
        state--this allows it to assume nothing for the next go-around (as this method
        is called in a loop elsewhere)
        """

        if self.verbose:
            print "\nCLIENT: sync_models"

        counters_to_download, counters_to_upload = self.sync_device_records()

        # Download (but prepare for errors--both thrown and unthrown!)
        download_results = {
            "saved_model_count" : 0,
            "unsaved_model_count" : 0,
        }
        try:

            if self.verbose:
                print "CLIENT: sync_models, downloading"

            response = json.loads(self.post("models/download", {"device_counters": counters_to_download}).content)
            # As usual, we're deserializing from the central server, so we assume that what we're getting
            #   is "smartly" dumbed down for us.  We don't need to specify the src_version, as it's
            #   pre-cleanaed for us.
            download_results.update(save_serialized_models(response.get("models", "[]"), verbose=self.verbose))
            self.session.models_downloaded += download_results["saved_model_count"]
            self.display_and_count_errors(download_results, context_name="downloading models")
        except Exception as e:
            print "Exception downloading models (in api_client): %s, %s, %s" % (e.__class__.__name__, e.message, e.args)
            download_results["error"] = e
            self.session.errors += 1

        # Upload (but prepare for errors--both thrown and unthrown!)
        upload_results = {
            "saved_model_count" : 0,
            "unsaved_model_count" : 0,
        }

        try:

            if self.verbose:
                print "CLIENT: sync_models, uploading"

            # By not specifying a dest_version, we're sending everything.
            #   Again, this is OK because we're sending to the central server.
            response = self.post("models/upload", {"models": get_serialized_models(counters_to_upload, verbose=self.verbose)})

            upload_results.update(json.loads(response.content))
            self.session.models_uploaded += upload_results["saved_model_count"]
            self.display_and_count_errors(upload_results, context_name="uploading models")
        except Exception as e:
            print "Exception uploading models (in api_client): %s, %s, %s" % (e.__class__.__name__, e.message, e.args)
            upload_results["error"] = e
            self.session.errors += 1

        self.session.save()

        return {"download_results": download_results, "upload_results": upload_results}
