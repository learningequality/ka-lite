import csv
import logging
import os

from django.template.defaultfilters import filesizeformat

from guppy import hpy

from base import Plugin

LOG = logging.getLogger("crawler")


class Heap(Plugin):
    """
    Calculate heap consumed before and after request
    """

    def __init__(self):
        super(Heap, self).__init__()
        self.heap_urls = self.data['heap_urls'] = {}
        self.hp = hpy()
        self.csv_writer = None

    def set_output_dir(self, output_dir=None):
        super(Heap, self).set_output_dir(output_dir)

        if output_dir:
            self.csv_writer = csv.writer(open(os.path.join(output_dir, 'heap.csv'), 'w'))

    def pre_request(self, sender, **kwargs):
        url = kwargs['url']
        self.hp.setrelheap()

    def post_request(self, sender, **kwargs):
        url = kwargs['url']
        heap = self.hp.heap()
        self.heap_urls[url] = heap.size

        LOG.debug("%s: heap consumed: %s", url, filesizeformat(self.heap_urls[url]))

        if self.csv_writer:
            self.csv_writer.writerow([url, heap.size])

    def finish_run(self, sender, **kwargs):
        "Print the most heap consumed by a view"

        alist = sorted(self.heap_urls.iteritems(),
            key=lambda (k,v): (v,k),
            reverse=True
        )

        for url, mem in alist[:10]:
            LOG.info("%s: %s heap", url, filesizeformat(mem))


PLUGIN = Heap