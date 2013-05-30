import csv
import logging
import os

from base import Plugin

LOG = logging.getLogger("crawler")

# from python mailing list http://mail.python.org/pipermail/python-list/2004-June/266257.html
_proc_status = '/proc/%d/status' % os.getpid()  # Linux only?
_scale = {'kB': 1024.0, 'mB': 1024.0*1024.0,
           'KB': 1024.0, 'MB': 1024.0*1024.0}

def _VmB(VmKey):
    global _scale
    try: # get the /proc/<pid>/status pseudo file
        t = open(_proc_status)
        v = [v for v in t.readlines() if v.startswith(VmKey)]
        t.close()
         # convert Vm value to bytes
        if len(v) == 1:
           t = v[0].split()  # e.g. 'VmRSS:  9999  kB'
           if len(t) == 3:  ## and t[0] == VmKey:
               return float(t[1]) * _scale.get(t[2], 0.0)
    except:
        pass
    return 0.0

def memory(since=0.0):
    '''Return process memory usage in bytes.
    '''
    return _VmB('VmSize:') - since

def stacksize(since=0.0):
    '''Return process stack size in bytes.
    '''
    return _VmB('VmStk:') - since


class Memory(Plugin):
    """
    Calculate proc memory consumed before and after request
    """
    active = False

    def __init__(self, write_csv=False):
        super(Memory, self).__init__()
        self.memory_urls = self.data['memory_urls'] = {}
        self.write_csv = write_csv
        if self.write_csv:
            self.csv_writer = csv.writer(open('memory.csv', 'w'))

    def pre_request(self, sender, **kwargs):
        url = kwargs['url']
        self.memory_urls[url] = memory()

    def post_request(self, sender, **kwargs):
        cur = memory()
        url = kwargs['url']
        old_memory = self.memory_urls[url]
        total_memory = cur - old_memory
        self.memory_urls[url] = total_memory
        LOG.info("Memory consumed: %s", self.memory_urls[url])
        if self.write_csv:
            self.csv_writer.writerow([url,cur, old_memory, total_memory])

    def finish_run(self, sender, **kwargs):
        "Print the most memory consumed by a view"
        alist = sorted(self.memory_urls.iteritems(), key=lambda (k,v): (v,k), reverse=True)
        for url, mem in alist[:10]:
            LOG.info("%s took %f of memory", url, mem)

PLUGIN = Memory