# encoding: utf-8
"""
HTML validation plugin which uses Jason Stitt's pytidylib wrapper for HTML Tidy

Prerequisites:
    tidylib: http://tidy.sourceforge.net/
    pytidylib: http://countergram.com/software/pytidylib/
"""

import logging
import re

import tidylib

from base import Plugin

# Based on http://stackoverflow.com/questions/92438/stripping-non-printable-characters-from-a-string-in-python
#
# We omit chars 9-13 (tab, newline, vertical tab, form feed, return) and 32
# (space) to avoid clogging our reports with warnings about common,
# non-problematic codes but still allow stripping things which will cause most
# XML parsers to choke

CONTROL_CHAR_RE = re.compile('[%s]' % "".join(
    re.escape(unichr(c)) for c in range(0, 8) + range(14, 31) + range(127, 160)
))

LOG = logging.getLogger("crawler")

class Tidy(Plugin):
    "Make sure your response is good"

    def post_request(self, sender, response, url=None, **kwargs):
        if not response['Content-Type'].startswith("text/html"):
            return

        # Check for redirects to avoid validation errors for empty responses:
        if response.status_code in (301, 302):
            return
        elif 400 <= response.status_code < 600:
            # We'll still validate error pages (they have user-written HTML, too)
            LOG.warning(
                "%s: Validating HTTP %d error page",
                url,
                response.status_code
            )
        elif response.status_code != 200:
            LOG.warning(
                "%s: Validating unusual HTTP %d response",
                url,
                response.status_code
            )

        # TODO: Decide how to handle character encodings more
        # intelligently - sniff? Scream bloody murder if charset isn't in
        # the HTTP headers?
        if response['Content-Type'] == "text/html; charset=utf-8":
            html = response.content.decode("utf-8")
        else:
            html = response.content

        if not html:
            LOG.error("%s: not processing empty response", url)
            return

        # First, deal with embedded control codes:
        html, sub_count = CONTROL_CHAR_RE.subn(" ", html)
        if sub_count:
            LOG.warning("%s: Stripped %d control characters from body: %s",
                url,
                sub_count,
                set(hex(ord(i)) for i in CONTROL_CHAR_RE.findall(html))
            )

        tidied_html, messages = tidylib.tidy_document(
            html.strip(),
            {
                "char-encoding":               "utf8",
                "clean":                        False,
                "drop-empty-paras":             False,
                "drop-font-tags":               False,
                "drop-proprietary-attributes":  False,
                "fix-backslash":                False,
                "indent":                       False,
                "output-xhtml":                 False,
            }
        )

        messages = filter(None, (l.strip() for l in messages.split("\n")))

        errors = []
        warnings = []

        for msg in messages:
            if "Error:" in msg:
                errors.append(msg)
            else:
                warnings.append(msg)

        if errors:
            LOG.error(
                "%s: HTML validation errors:\n\t%s",
                url,
                "\n\t".join(errors)
            )

        if warnings:
            LOG.warning(
                "%s: HTML validation warnings:\n\t%s",
                url,
                "\n\t".join(warnings)
            )


PLUGIN = Tidy