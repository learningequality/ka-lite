from HTMLParser import HTMLParseError
import logging
import os
import urlparse
import urllib

from django.conf import settings
from django.db import transaction
from django.views.debug import cleanse_setting
from django.test.client import Client as DjangoClient
from django.test.utils import setup_test_environment, teardown_test_environment

from crawler import signals as test_signals
from crawler.plugins.base import Plugin
from utils import caching # kalite function


import urllib
class Client(object):
    def __init__(self, REMOTE_ADDR='127.0.0.1', REMOTE_PORT=8008):
        self.ra = "%s:%d" % (REMOTE_ADDR, REMOTE_PORT)
        self.dc = DjangoClient(REMOTE_ADDR)
    
    # Implement cached-page-only crawling
    def get(self, base_url, *args, **kwargs):

        full_url = "http://"+self.ra+base_url

        # force the cache, only if it doesn't already exist
        if not caching.has_cache_key(path=base_url):
            urllib.urlopen(full_url).close() 
        
        # Only follow objects that are cacheable
        if caching.has_cache_key(path=base_url):
            print full_url
            return self.dc.get(base_url) # return what's expected
        else:
            return None


#Used for less useful debug output.
SUPER_DEBUG = 5

LOG = logging.getLogger('crawler')

try:
    import lxml.html
    def link_extractor(html):
        try:
            tree = lxml.html.document_fromstring(html)
        except lxml.etree.ParseError, e:
            raise HTMLParseError(str(e), e.position)

        for element, attribute, link, pos in tree.iterlinks():
            yield link
except ImportError:
    LOG.info("Processing documents with HTMLParser; install lxml for greater performance")

    from HTMLParser import HTMLParser

    def link_extractor(html):
        class LinkExtractor(HTMLParser):
            links = set()

            def handle_starttag(self, tag, attrs):
                self.links.update(
                    v for k, v in attrs if k == "href" or k =="src"
                )

        parser = LinkExtractor()
        parser.feed(html)
        parser.close()

        return parser.links


class Crawler(object):
    """
    This is a class that represents a URL crawler in python
    """

    def __init__(self, base_url, conf_urls={}, verbosity=1, output_dir=None, ascend=True, **kwargs):
        self.base_url = base_url
        self.conf_urls = conf_urls
        self.verbosity = verbosity
        self.ascend = ascend

        auth = kwargs.get('auth')
        remote_addr = kwargs.get("remote_host", "127.0.0.1")
        remote_port = int(kwargs.get("remote_port", "8008"))

        if output_dir:
            assert os.path.isdir(output_dir)
            self.output_dir = os.path.realpath(output_dir)
            LOG.info("Output will be saved to %s" % self.output_dir)
        else:
            self.output_dir = None

        #These two are what keep track of what to crawl and what has been.
        self.not_crawled = [(0, 'START',self.base_url)]
        self.crawled = {}

        self.c = Client(REMOTE_ADDR=remote_addr, REMOTE_PORT=remote_port)

        if auth:
            printable_auth = ', '.join(
                '%s: %s' % (key, cleanse_setting(key.upper(), value))
                for key, value in auth.items())
            LOG.info('Log in with %s' % printable_auth)
            self.c.login(**auth)

        self.plugins = []
        for plug in Plugin.__subclasses__():
            active = getattr(plug, 'active', True)
            if active:
                #TODO: Check if plugin supports writing CSV (or to a file in general?)
                self.plugins.append(plug())

    def _parse_urls(self, url, resp):
        parsed = urlparse.urlparse(url)

        if resp['Content-Type'] == "text/html; charset=utf-8":
            html = resp.content.decode("utf-8")
        else:
            html = resp.content

        returned_urls = []

        for link in link_extractor(html):
            parsed_href = urlparse.urlparse(link)

            if not parsed_href.path:
                continue

            if parsed_href.scheme and not parsed_href.netloc.startswith("testserver"):
                LOG.log(SUPER_DEBUG, "Skipping external link: %s", link)
                continue

            if ('django.contrib.staticfiles' in settings.INSTALLED_APPS
                and parsed_href.path.startswith(settings.STATIC_URL)):
                LOG.debug("Skipping static file %s", parsed_href.path)
            elif parsed_href.path.startswith('/'):
                returned_urls.append(link)
            else:
                # We'll use urlparse's urljoin since that handles things like <a href="../foo">
                returned_urls.append(urlparse.urljoin(url, link))

        return returned_urls

    def get_url(self, from_url, to_url):
        """
        Takes a url, and returns it with a list of links
        This uses the Django test client.
        """
        parsed = urlparse.urlparse(to_url)
        request_dict = dict(urlparse.parse_qsl(parsed.query))
        url_path = parsed.path

        #url_path now contains the path, request_dict contains get params

        LOG.debug("%s: link to %s with parameters %s", from_url, to_url, request_dict)

        test_signals.pre_request.send(self, url=to_url, request_dict=request_dict)

        resp = self.c.get(url_path, request_dict, follow=False)
        if not resp:
            return None
            
        test_signals.post_request.send(self, url=to_url, response=resp)

        if resp.status_code in (301, 302):
            location = resp["Location"]
            if location.startswith("http://testserver"):
                LOG.debug("%s: following redirect to %s", to_url, location)
                # Mmm, recursion TODO: add a max redirects limit?
                return self.get_url(from_url, location)
            else:
                LOG.info("%s: not following off-site redirect to %s", to_url, location)
                return (resp, ())
        elif 400 <= resp.status_code < 600:
            # We'll avoid logging a warning for HTTP statuses which aren't in the
            # official error ranges:
            LOG.warning("%s links to %s, which returned HTTP status %d", from_url, url_path, resp.status_code)
            return (resp, ())

        if resp['Content-Type'].startswith("text/html"):
            returned_urls = self._parse_urls(to_url, resp)
            test_signals.urls_parsed.send(self, fro=to_url, returned_urls=returned_urls)
        else:
            returned_urls = list()

        return (resp, returned_urls)

    def run(self, max_depth=3):
        for p in self.plugins:
            p.set_output_dir(self.output_dir)

        old_DEBUG = settings.DEBUG
        settings.DEBUG = False

        setup_test_environment()
        test_signals.start_run.send(self)

        # To avoid tainting our memory usage stats with startup overhead we'll
        # do one extra request for the first page now:
        self.c.get(self.not_crawled[0][-1])

        while self.not_crawled:
            #Take top off not_crawled and evaluate it
            current_depth, from_url, to_url = self.not_crawled.pop(0)
            if current_depth > max_depth:
                continue

            transaction.enter_transaction_management()
            try:
                resp, returned_urls = self.get_url(from_url, to_url)
            except HTMLParseError, e:
                LOG.error("%s: unable to parse invalid HTML: %s", to_url, e)
            except TypeError as e:
                if getattr(e, 'message',"") == "'NoneType' object is not iterable":
                    LOG.info("%s: not a cacheable page" % to_url)
                    continue
                else:
                    raise e
            except Exception, e:
                LOG.exception("%s had unhandled exception: %s", to_url, e)
                continue
            finally:
                transaction.rollback()

            self.crawled[to_url] = True
            #Find its links that haven't been crawled
            for base_url in returned_urls:
                if not self.ascend and not base_url.startswith(self.base_url):
                    LOG.log(SUPER_DEBUG, "Skipping %s - outside scope of %s", base_url, self.base_url)
                    continue

                if base_url not in [to for dep,fro,to in self.not_crawled] and not self.crawled.has_key(base_url):
                    self.not_crawled.append((current_depth+1, to_url, base_url))

        test_signals.finish_run.send(self)

        teardown_test_environment()

        settings.DEBUG = old_DEBUG
