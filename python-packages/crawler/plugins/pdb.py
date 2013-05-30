import logging

from base import Plugin

LOG = logging.getLogger("crawler")

class Pdb(Plugin):
    "Run pdb on fail"
    active = False

    def post_request(self, sender, **kwargs):
        url = kwargs['url']
        resp = kwargs['response']
        if hasattr(resp, 'status_code'):
            if not resp.status_code in (200, 302, 301):
                LOG.error("%s: Status Code: %s", url, resp.status_code)
                try:
                    import ipdb; ipdb.set_trace()
                except ImportError:
                    import pdb; pdb.set_trace()

PLUGIN = Pdb