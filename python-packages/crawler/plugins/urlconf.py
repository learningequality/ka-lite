import logging
import re

from base import Plugin

LOG = logging.getLogger("crawler")

class URLConf(Plugin):
    """
    Plugin to check validity of URLConf.
    Run after the spider is done to show what URLConf entries got hit.
    """

    def finish_run(self, sender, **kwargs):
        normal_patterns = list()
        admin_patterns = list()

        for pattern in sender.conf_urls.keys():
            pattern = pattern.replace('^', '').replace('$', '').replace('//', '/')
            curr = re.compile(pattern)

            if any(curr.search(url) for url in sender.crawled):
                continue

            if pattern.startswith("admin"):
                admin_patterns.append(pattern)
            else:
                normal_patterns.append(pattern)

        if admin_patterns:
            LOG.debug("These admin pages were not crawled: %s", "\n\t".join(sorted(admin_patterns)))

        if normal_patterns:
            LOG.info("These patterns were not matched during the crawl: %s", "\n\t".join(sorted(normal_patterns)))

PLUGIN = URLConf