import logging

from BeautifulSoup import BeautifulSoup

from base import Plugin

LOG = logging.getLogger("crawler")

class Sanitize(Plugin):
    "Make sure your response is good"

    def post_request(self, sender, response, **kwargs):
        if not response['Content-Type'].startswith("text/html"):
            return

        if response['Content-Type'] == "text/html; charset=utf-8":
            html = response.content.decode("utf-8")
        else:
            html = response.content

        try:
            soup = BeautifulSoup(html)
            if soup.find(text='&lt;') or soup.find(text='&gt;'):
                LOG.warning("%s has dirty html", kwargs['url'])
        except Exception, e:
            # TODO: Derive unique names so we can continue after errors without clobbering past error pages
            fo = open("temp.html", 'w')
            fo.write(kwargs['response'].content)
            fo.close()
            LOG.error('Saved bad html to file temp.html')
            raise e


PLUGIN = Sanitize