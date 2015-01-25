"""
"""
import json
import requests
import urllib
import urllib2
import uuid

from django.conf import settings

logging = settings.LOG


class BaseClient(object):

    def __init__(self, host="%s://%s/" % (settings.SECURESYNC_PROTOCOL,settings.CENTRAL_SERVER_HOST), require_trusted=True, verbose=True):
        self.parsed_url = urllib2.urlparse.urlparse(host)
        self.url = "%s://%s" % (self.parsed_url.scheme, self.parsed_url.netloc)
        self.require_trusted = require_trusted
        self.verbose = verbose

    def path_to_url(self, path):
        if path.startswith("/"):
            return self.url + path
        else:
            return self.url + "/securesync/api/" + path

    def post(self, path, payload={}, *args, **kwargs):
        if self.verbose:
            print "CLIENT: post %s" % path
        return requests.post(self.path_to_url(path), data=json.dumps(payload))

    def get(self, path, payload={}, *args, **kwargs):
        # add a random parameter to ensure the request is not cached
        payload["_"] = uuid.uuid4().hex
        query = urllib.urlencode(payload)
        if self.verbose:
            logging.debug("CLIENT: get %s" % path)
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
