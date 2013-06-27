import logging
import re
import json
import requests
import urllib
import urllib2
import uuid

from django.core import serializers

import crypto
import settings
import kalite
import model_sync
from models import *


class SyncClient(object):
    """ This is for the distributed server, for establishing a client session with
    the central server.  Over that session, syncing can occur in multiple requests.
    
    Note that in the future, this object may be used to sync 
    between two distributed servers (i.e. peer-to-peer sync)!"""
     
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


    def register(self, prove_self=False):
        """Register this device with a zone."""
        
        # Get the required model data by registering (online and offline options available)
        try:
            if prove_self:
                (models,response) = self.register_confirm_self_registration()
            else:
                models = self.register_via_remote()
        except Exception as e:
            # Some of our exceptions are actually json blobs from the server.
            #   Try loading them to pass on that error info.
            try:
                return json.loads(e.message)
            except:
                return { "code": "unexpected_exception", "error": e.message }
        
        # If we got here, we've successfully registered, and 
        #   have the model data necessary for completing registration!
        for model in models:
            # BUG(bcipolli)
            # Shouldn't we care when things fail to verify??
            if not model.object.verify():
                logging.warn("\n\n\nFailed to verify model: %s!\n\n\n" % str(model.object))
                
            # save the imported model, and mark the returned Device as trusted
            if isinstance(model.object, Device):
                model.object.save(is_trusted=True, imported=True)
            else:
                model.object.save(imported=True)
        
        # If that all completes successfully, then we've registered!  Woot!
        return {"code": "registered"}


    def register_confirm_self_registration(self):
        own_device = Device.get_own_device()
        own_zone = DeviceZone.objects.get(device=own_device).zone
        own_zone_key = ZoneKey.objects.get(zone=own_zone)# get_object_or_None(ZoneKey, zone=own_zone) # or should I raise if not found?
        install_certs = ZoneInstallCertificate.objects.filter(zone=own_zone)
        if not install_certs:
            try:
                install_certs = own_zone.generate_install_certificates(num_certificates=1)
            except:
                pass

        if not install_certs:
            raise Exception("You shouldn't ask to self-register with the central server, when you don't have any install certificates to validate yourself with!")                

        # For now, just try with one certificate
        r = self.post("register", {
            "client_device": serializers.serialize("json", [own_device, own_zone, own_zone_key, install_certs[0]], ensure_ascii=False),
        })
    
        # Failed to register with any certificate
        if r.status_code != 200:
            raise Exception(r.content)

        # When we register, we should receive the model information we require.
        return (serializers.deserialize("json", r.content), r)


    def register_via_remote(self):
        """Register this device with a zone, through the central server directly"""
        
        own_device = Device.get_own_device()

        r = self.post("register", {
            "client_device": serializers.serialize("json", [own_device], ensure_ascii=False),
        })

        # Failed to register with any certificate
        if r.status_code != 200:
            raise Exception(r.content)

        # When we register, we should receive the model information we require.
        return serializers.deserialize("json", r.content)
        
    
    def start_session(self):
        if self.session:
            self.close_session()
        self.session = SyncSession()
        
        # Request one: validate me as a sessionable partner
        (self.session.client_nonce, 
         self.session.client_device,
         data) = self.validate_me_on_server()

        # Able to create session
        signature = data.get("signature", "")
        session = serializers.deserialize("json", data["session"], server_version=kalite.VERSION).next().object
        self.session.server_nonce = session.server_nonce
        self.session.server_device = session.server_device
        if not session.verify_server_signature(signature):
            raise Exception("Sever session signature did not match.")
        if session.client_nonce != self.session.client_nonce:
            raise Exception("Client session nonce did not match.")
        if session.client_device != self.session.client_device:
            raise Exception("Client session device did not match.")
        if self.require_trusted and not session.server_device.get_metadata().is_trusted:
            raise Exception("The server is not trusted, don't make a session with THAT.")
        self.session.verified = True
        self.session.timestamp = session.timestamp
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
            "client_version": kalite.VERSION,
            "client_os": kalite.OS,
        })
        
        raw_data = r.content
        try:
            data = json.loads(raw_data)
        except ValueError as e:
            z = re.search(r'exception_value">([^<]+)<', str(raw_data), re.MULTILINE)
            if z:
                raise Exception("Could not load JSON\n; server error=%s" % z.group(1))
            else:
                raise Exception("Could not load JSON\n; raw content=%s" % raw_data)
            
        # Happens if the server has an error
        if data.get("error", ""):
            # This happens when a device points to a new central server,
            #   either because it changed, or because it self-registered.
            if not recursive_retry and 0 == data["error"].find("Client device matching id could not be found."):
                resp = self.register(prove_self=True)
                if resp.get("error", "") != "":
                    raise Exception("Error [code=%s]: %s" % (resp.get("code",""), resp.get("error","")))
                elif resp.get("code","") != "registered":
                    raise Exception("Unexpected code: '%s'" % resp.get("code",""))
                return self.validate_me_on_server(recursive_retry=True)
            raise Exception(data.get("error", ""))

        return (client_nonce, client_device, data)
        

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
            response = self.post("models/upload", {"models": model_sync.get_serialized_models(self.counters_to_upload, client_version=self.session.client_version)})
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
