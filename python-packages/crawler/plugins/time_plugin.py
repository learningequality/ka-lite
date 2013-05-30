import time
import logging

from base import Plugin

LOG = logging.getLogger('crawler')

class Time(Plugin):
    """
    Follow the time it takes to run requests.
    """

    def __init__(self):
        super(Time, self).__init__()
        self.timed_urls = self.data['timed_urls'] = {}

    def pre_request(self, sender, **kwargs):
        url = kwargs['url']
        self.timed_urls[url] = time.time()

    def post_request(self, sender, **kwargs):
        cur = time.time()
        url = kwargs['url']
        old_time = self.timed_urls[url]
        total_time = cur - old_time
        self.timed_urls[url] = total_time
        LOG.debug("Time taken: %s", self.timed_urls[url])

    def finish_run(self, sender, **kwargs):
        "Print the longest time it took for pages to load"
        alist = sorted(self.timed_urls.iteritems(), key=lambda (k,v): (v,k), reverse=True)
        for url, ttime in alist[:10]:
            LOG.info("%s took %f", url, ttime)

PLUGIN = Time