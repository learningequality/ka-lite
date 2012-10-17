import re, json, requests, urllib2, uuid

from models import SyncSession, Device, RegisteredDevicePublicKey, json_serializer, get_device_counters, save_serialized_models

class SyncClient(object):
    session = None
    
    def post(self, path, payload):
        return requests.post(self.url + path, data=json.dumps(payload))
    
    def start_session(self, host="http://127.0.0.1:8000"):
        url = urllib2.urlparse.urlparse(host)
        self.url = "%s://%s/securesync/api/" % (url.scheme, url.netloc)
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


