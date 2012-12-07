from models import *

import re, json, requests, urllib, urllib2, uuid
from django.core import serializers

import crypto
import settings
import kalite

class SyncClient(object):
    session = None
    counters_to_download = None
    counters_to_upload = None
    
    def __init__(self, host=settings.CENTRAL_SERVER_HOST, require_trusted=True):
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
        own_device = Device.get_own_device()
        r = self.post("register", {
            "client_device": json_serializer.serialize([own_device], ensure_ascii=False)
        })
        if r.status_code == 200:
            models = serializers.deserialize("json", r.content)
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
        data = json.loads(r.content)
        if data.get("error", ""):
            raise Exception(data.get("error", ""))
        signature = data.get("signature", "")
        session = serializers.deserialize("json", data["session"]).next().object
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
        return get_device_counters(self.session.client_device.get_zone())

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
                self.counters_to_upload[device] = server_counters[device] + 1
        
        for device in server_counters:
            if device not in client_counters:
                devices_to_download.append(device)
                self.counters_to_download[device] = 0
            elif server_counters[device] > client_counters[device]:
                self.counters_to_download[device] = client_counters[device] + 1

        response = json.loads(self.post("device/download", {"devices": devices_to_download}).content)
        download_results = save_serialized_models(response.get("devices", "[]"))
        
        self.session.models_downloaded += download_results["saved_model_count"]
        
        # TODO(jamalex): upload local devices as well? only needed once we have P2P syncing
        
    def sync_models(self):

        if self.counters_to_download is None or self.counters_to_upload is None:
            self.sync_device_records()
            
        response = json.loads(self.post("models/download", {"device_counters": self.counters_to_download}).content)
        download_results = save_serialized_models(response.get("models", "[]"))
        
        self.session.models_downloaded += download_results["saved_model_count"]
        
        response = self.post("models/upload", {"models": get_serialized_models(self.counters_to_upload)})
        upload_results = json.loads(response.content)
        
        self.session.models_uploaded += upload_results["saved_model_count"]
        
        self.counters_to_download = None
        self.counters_to_upload = None
        
        return {"download_results": download_results, "upload_results": upload_results}
