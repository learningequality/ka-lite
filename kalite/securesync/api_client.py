import re, json, requests, urllib2, uuid

from models import SyncSession, Device, RegisteredDevicePublicKey, json_serializer, get_device_counters, save_serialized_models
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
            if self.get("test", timeout=5).text != "OK":
                return "bad_address"
            return "success"
        except requests.ConnectionError:
            return "connection_error"
        except Exception:
            return "error"
        
    def register(self):
        r = self.post("register", {
            "public_key": Device.get_own_device().public_key
        })
        if r.status_code == 200:
            return "registered"
        return json.loads(r.text).get("code")
    
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
        
        
    def close_session(self):
        if not self.session:
            return
        self.post("session/destroy", {
            "client_nonce": self.session.client_nonce
        })


