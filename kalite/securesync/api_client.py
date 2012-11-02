import re, json, requests, urllib2, uuid
from django.core import serializers

from models import SyncSession, Device, RegisteredDevicePublicKey, json_serializer, get_device_counters, save_serialized_models
import crypto
import settings


class SyncClient(object):
    session = None
    
    def __init__(self, host=settings.CENTRAL_SERVER_HOST):
        url = urllib2.urlparse.urlparse(host)
        self.url = "%s://%s" % (url.scheme, url.netloc)        
    
    def path_to_url(self, path):
        if path.startswith("/"):
            return self.url + path
        else:
            return self.url + "/securesync/api/" + path
    
    def post(self, path, payload="", *args, **kwargs):
        return requests.post(self.path_to_url(path), data=json.dumps(payload))

    def get(self, path, *args, **kwargs):
        return requests.get(self.path_to_url(path), *args, **kwargs)
        
    def test_connection(self):
        try:
            if self.get("test", timeout=5).content != "OK":
                return "bad_address"
            return "success"
        except requests.ConnectionError:
            return "connection_error"
        except Exception:
            return "error"
            
    def register(self):
        own_device = Device.get_own_device()
        r = self.post("register", {
            "client_device": json_serializer.serialize([own_device], ensure_ascii=False, indent=2)
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
            return "registered"
        return json.loads(r.content).get("code")
    
    def start_session(self):
        if self.session:
            self.close_session()
        self.session = SyncSession()
        self.session.client_nonce = uuid.uuid4().hex
        self.session.client_device = Device.get_own_device()
        r = self.post("session/create", {
            "client_nonce": self.session.client_nonce,
            "client_device": self.session.client_device.pk,
        })
        data = json.loads(r.content)
        signature = data.get("signature", "")
        session = serializers.deserialize("json", data["session"]).next().object
        if not session.verify_server_signature(signature):
            raise Exception("Signature did not match.")
        if session.client_nonce != self.session.client_nonce:
            raise Exception("Client nonce did not match.")
        if session.client_device != self.session.client_device:
            raise Exception("Client device did not match.")
        if not session.server_device.get_metadata().is_trusted:
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
            "signature": session.sign(),
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
        return "success"


