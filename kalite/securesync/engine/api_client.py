import re
import json
import uuid

import kalite
import settings
from . import get_serialized_models, save_serialized_models, get_device_counters, deserialize
from .models import *
from securesync.api_client import BaseClient
from securesync.devices.api_client import RegistrationClient
from securesync.devices.models import *
from settings import LOG as logging


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

        if self.session:
            self.close_session()
        self.session = SyncSession()

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
            "client_os": kalite.OS,
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
        if not self.session:
            return
        self.post("session/destroy", {
            "client_nonce": self.session.client_nonce
        })
        self.session = None
        return "success"

    def get_server_device_counters(self):
        r = self.get("device/counters")
        return json.loads(r.content or "{}").get("device_counters", {})

    def get_client_device_counters(self):
        return get_device_counters(zone=self.session.client_device.get_zone())


    def sync_device_records(self):

        server_counters = self.get_server_device_counters()
        client_counters = self.get_client_device_counters()

        devices_to_download = []
        devices_to_upload = []

        counters_to_download = {}
        counters_to_upload = {}

        for device_id in client_counters:
            if device_id not in server_counters:
                devices_to_upload.append(device_id)
                counters_to_upload[device_id] = 0
            elif client_counters[device_id] > server_counters[device_id]:
                counters_to_upload[device_id] = server_counters[device_id]

        for device_id in server_counters:
            if device_id not in client_counters:
                devices_to_download.append(device_id)
                counters_to_download[device_id] = 0
            elif server_counters[device_id] > client_counters[device_id]:
                counters_to_download[device_id] = client_counters[device_id]

        response = json.loads(self.post("device/download", {"devices": devices_to_download}).content)
        # As usual, we're deserializing from the central server, so we assume that what we're getting
        #   is "smartly" dumbed down for us.  We don't need to specify the src_version, as it's
        #   pre-cleaned for us.
        download_results = save_serialized_models(response.get("devices", "[]"), increment_counters=False)

        # BUGFIX(bcipolli) metadata only gets created if models are
        #   streamed; if a device is downloaded but no models are downloaded,
        #   metadata does not exist.  Let's just force it here.
        for device_id in devices_to_download: # force
            try:
                d = Device.objects.get(id=device_id)
            except Exception as e:
                logging.error("Exception locating device %s for metadata creation: %s" % (device_id, e))
                continue

            if not d.get_counter_position():  # this would be nonzero if the device sync'd models
                d.set_counter_position(counters_to_download[device_id])

        self.session.models_downloaded += download_results["saved_model_count"]
        self.session.errors += download_results.has_key("error")

        self.session.save()

        # TODO(jamalex): upload local devices as well? only needed once we have P2P syncing

        return (counters_to_download, counters_to_upload)


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

        counters_to_download, counters_to_upload = self.sync_device_records()

        # Download (but prepare for errors--both thrown and unthrown!)
        download_results = {
            "saved_model_count" : 0,
            "unsaved_model_count" : 0,
        }
        try:
            response = json.loads(self.post("models/download", {"device_counters": counters_to_download}).content)
            # As usual, we're deserializing from the central server, so we assume that what we're getting
            #   is "smartly" dumbed down for us.  We don't need to specify the src_version, as it's
            #   pre-cleanaed for us.
            download_results = save_serialized_models(response.get("models", "[]"))
            self.session.models_downloaded += download_results["saved_model_count"]
            self.session.errors += download_results.has_key("error")
            self.session.errors += download_results.has_key("exceptions")
        except Exception as e:
            logging.debug("Exception downloading models: %s" % e)
            download_results["error"] = e
            self.session.errors += 1

        # Upload (but prepare for errors--both thrown and unthrown!)
        upload_results = {
            "saved_model_count" : 0,
            "unsaved_model_count" : 0,
        }
        try:
            # By not specifying a dest_version, we're sending everything.
            #   Again, this is OK because we're sending to the central server.
            response = self.post("models/upload", {"models": get_serialized_models(counters_to_upload)})
            upload_results = json.loads(response.content)
            self.session.models_uploaded += upload_results["saved_model_count"]
            self.session.errors += upload_results.has_key("error")
            self.session.errors += upload_results.has_key("exceptions")
        except Exception as e:
            logging.debug("Exception uploading models: %s" % e)
            upload_results["error"] = e
            self.session.errors += 1

        self.session.save()

        return {"download_results": download_results, "upload_results": upload_results}
