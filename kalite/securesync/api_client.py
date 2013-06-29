import re
import json
import requests
import urllib
import urllib2
import uuid

from django.core import serializers

import kalite
import settings
from kalite.utils.internet import am_i_online
from securesync import crypto, model_sync
from securesync.models import *


class SyncClient(object):
    """ This is for the distributed server, for establishing a client session with
    the central server.  Over that session, syncing can occur in multiple requests"""

    session = None
    counters_to_download = None
    counters_to_upload = None

    def __init__(self, host="%s://%s/"%(settings.SECURESYNC_PROTOCOL,settings.CENTRAL_SERVER_HOST), require_trusted=True):
        url = urllib2.urlparse.urlparse(host)
        self.url = "%s://%s" % (url.scheme, url.netloc)
        self.require_trusted = require_trusted

    def path_to_url(self, path):
        if path.startswith("/"):
            return self.url + path
        else:
            return self.url + "/securesync/api/" + path

    def post(self, path, payload={}, *args, **kwargs):
        if self.session and self.session.client_nonce:
            payload["client_nonce"] = self.session.client_nonce
        return requests.post(self.path_to_url(path), data=json.dumps(payload))

    def get(self, path, payload={}, *args, **kwargs):
        if self.session and self.session.client_nonce:
            payload["client_nonce"] = self.session.client_nonce
        # add a random parameter to ensure the request is not cached
        payload["_"] = uuid.uuid4().hex
        query = urllib.urlencode(payload)
        return requests.get(self.path_to_url(path) + "?" + query, *args, **kwargs)

    def test_connection(self):
        try:
            if self.get("test", timeout=5).content != "OK":
                return "bad_address"
            return "success"
        except requests.ConnectionError:
            return "connection_error"
        except Exception as e:
            return "error (%s)" % e

    def register(self):
        """Register a device with the central server.  Happens outside of a session."""

        own_device = Device.get_own_device()
        # Since we can't know the version of the remote device (yet),
        #   we give it everything we possibly can (don't specify a dest_version)
        #
        # Note that (currently) this should never fail--the central server (which we're sending
        #   these objects to) should always have a higher version.
        r = self.post("register", {
            "client_device": serializers.serialize("json", [own_device], ensure_ascii=False)
        })
        # If they don't understand, our assumption is broken.
        if r.status_code == 500:
            if "Device has no field named 'version'" in r.content:
                raise Exception("Central server is of an older version than us?")
            else:
                raise Exception("Error registering with central server: %s" % r.content)

        elif r.status_code == 200:
            # Save to our local store.  By NOT passing a src_version, 
            #   we're saying it's OK to just store what we can.
            models = serializers.deserialize("json", r.content, src_version=None, dest_version=own_device.version)
            for model in models:
                if not model.object.verify():
                    continue
                # save the imported model, and mark the returned Device as trusted
                if isinstance(model.object, Device):
                    model.object.save(is_trusted=True, imported=True)
                else:
                    model.object.save(imported=True)
            return {"code": "registered"}
        return json.loads(r.content)

    def start_session(self):
        """A 'session' to exchange data"""
        
        if self.session:
            self.close_session()
        self.session = SyncSession()
        self.session.client_nonce = uuid.uuid4().hex
        self.session.client_device = Device.get_own_device()
        r = self.post("session/create", {
            "client_nonce": self.session.client_nonce,
            "client_device": self.session.client_device.pk,
            "client_version": kalite.VERSION,
            "client_os": kalite.OS,
        })

        # Happens if the server has an error
        raw_data = r.content
        try:
            data = json.loads(raw_data)
        except ValueError as e:
            z = re.search(r'exception_value">([^<]+)<', str(raw_data), re.MULTILINE)
            if z:
                raise Exception("Could not load JSON\n; server error=%s" % z.group(1))
            else:
                raise Exception("Could not load JSON\n; raw content=%s" % raw_data)

        if data.get("error", ""):
            raise Exception(data.get("error", ""))
        signature = data.get("signature", "")
        # Once again, we assume that (currently) the central server's version is >= ours,
        #   We just store what we can.
        own_device = self.session.client_device
        session = serializers.deserialize("json", data["session"], src_version=None, dest_version=own_device.version).next().object
        if not session.verify_server_signature(signature):
            raise Exception("Signature did not match.")
        if session.client_nonce != self.session.client_nonce:
            raise Exception("Client nonce did not match.")
        if session.client_device != self.session.client_device:
            raise Exception("Client device did not match.")
        if self.require_trusted and not session.server_device.get_metadata().is_trusted:
            raise Exception("The server is not trusted.")
        self.session.server_nonce = session.server_nonce
        self.session.server_device = session.server_device
        self.session.verified = True
        self.session.timestamp = session.timestamp
        self.session.save()

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

    def close_session(self):
        if not self.session:
            return
        self.post("session/destroy", {
            "client_nonce": self.session.client_nonce
        })
        self.session.delete()
        self.session = None
        return "success"

    def get_server_device_counters(self):
        r = self.get("device/counters")
        return json.loads(r.content or "{}").get("device_counters", {})

    def get_client_device_counters(self):
        return Device.get_device_counters(self.session.client_device.get_zone())

    def sync_device_records(self):

        server_counters = self.get_server_device_counters()
        client_counters = self.get_client_device_counters()

        devices_to_download = []
        devices_to_upload = []

        self.counters_to_download = {}
        self.counters_to_upload = {}

        for device in client_counters:
            if device not in server_counters:
                devices_to_upload.append(device)
                self.counters_to_upload[device] = 0
            elif client_counters[device] > server_counters[device]:
                self.counters_to_upload[device] = server_counters[device]

        for device in server_counters:
            if device not in client_counters:
                devices_to_download.append(device)
                self.counters_to_download[device] = 0
            elif server_counters[device] > client_counters[device]:
                self.counters_to_download[device] = client_counters[device]
                
        response = json.loads(self.post("device/download", {"devices": devices_to_download}).content)
        download_results = model_sync.save_serialized_models(response.get("devices", "[]"), increment_counters=False)

        # BUGFIX(bcipolli) metadata only gets created if models are 
        #   streamed; if a device is downloaded but no models are downloaded,
        #   metadata does not exist.  Let's just force it here.
        for device_id in devices_to_download: # force
            try:
                d = Device.objects.get(id=device_id)
            except:
                continue
            dm = d.get_metadata() 
            if not dm.counter_position: # this would be nonzero if the device sync'd models
                dm.counter_position = self.counters_to_download[device_id]
            dm.save()

        self.session.models_downloaded += download_results["saved_model_count"]
        self.session.errors += download_results.has_key("error")

        # TODO(jamalex): upload local devices as well? only needed once we have P2P syncing
    def sync_models(self):

        if self.counters_to_download is None or self.counters_to_upload is None:
            self.sync_device_records()

        # Download (but prepare for errors--both thrown and unthrown!)
        download_results = {
            "saved_model_count" : 0,
            "unsaved_model_count" : 0,
        }
        try:
            response = json.loads(self.post("models/download", {"device_counters": self.counters_to_download}).content)
            download_results = model_sync.save_serialized_models(response.get("models", "[]"))
            self.session.models_downloaded += download_results["saved_model_count"]
            self.session.errors += download_results.has_key("error")
            self.session.errors += download_results.has_key("exceptions")
        except Exception as e:
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
            response = self.post("models/upload", {"models": model_sync.get_serialized_models(self.counters_to_upload)})
            upload_results = json.loads(response.content)
            self.session.models_uploaded += upload_results["saved_model_count"]
            self.session.errors += upload_results.has_key("error")
            self.session.errors += upload_results.has_key("exceptions")
        except Exception as e:
            upload_results["error"] = e
            self.session.errors += 1

        self.counters_to_download = None
        self.counters_to_upload = None

        return {"download_results": download_results, "upload_results": upload_results}
