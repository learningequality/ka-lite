from __future__ import unicode_literals

import calendar
import datetime
import re
import sys
try:
    from urllib import parse as urllib_parse
except ImportError:     # Python 2
    import urllib as urllib_parse
    import urlparse
    urllib_parse.urlparse = urlparse.urlparse


from email.utils import formatdate

from django.utils.datastructures import MultiValueDict
from django.utils.encoding import force_str, force_text
from django.utils.functional import allow_lazy
from django.utils import six

ETAG_MATCH = re.compile(r'(?:W/)?"((?:\\.|[^"])*)"')

MONTHS = 'jan feb mar apr may jun jul aug sep oct nov dec'.split()
__D = r'(?P<day>\d{2})'
__D2 = r'(?P<day>[ \d]\d)'
__M = r'(?P<mon>\w{3})'
__Y = r'(?P<year>\d{4})'
__Y2 = r'(?P<year>\d{2})'
__T = r'(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})'
RFC1123_DATE = re.compile(r'^\w{3}, %s %s %s %s GMT$' % (__D, __M, __Y, __T))
RFC850_DATE = re.compile(r'^\w{6,9}, %s-%s-%s %s GMT$' % (__D, __M, __Y2, __T))
ASCTIME_DATE = re.compile(r'^\w{3} %s %s %s %s$' % (__M, __D2, __T, __Y))

def urlquote(url, safe='/'):
    """
    A version of Python's urllib.quote() function that can operate on unicode
    strings. The url is first UTF-8 encoded before quoting. The returned string
    can safely be used as part of an argument to a subsequent iri_to_uri() call
    without double-quoting occurring.
    """
    return force_text(urllib_parse.quote(force_str(url), force_str(safe)))
urlquote = allow_lazy(urlquote, six.text_type)

def urlquote_plus(url, safe=''):
    """
    A version of Python's urllib.quote_plus() function that can operate on
    unicode strings. The url is first UTF-8 encoded before quoting. The
    returned string can safely be used as part of an argument to a subsequent
    iri_to_uri() call without double-quoting occurring.
    """
    return force_text(urllib_parse.quote_plus(force_str(url), force_str(safe)))
urlquote_plus = allow_lazy(urlquote_plus, six.text_type)

def urlunquote(quoted_url):
    """
    A wrapper for Python's urllib.unquote() function that can operate on
    the result of django.utils.http.urlquote().
    """
    return force_text(urllib_parse.unquote(force_str(quoted_url)))
urlunquote = allow_lazy(urlunquote, six.text_type)

def urlunquote_plus(quoted_url):
    """
    A wrapper for Python's urllib.unquote_plus() function that can operate on
    the result of django.utils.http.urlquote_plus().
    """
    return force_text(urllib_parse.unquote_plus(force_str(quoted_url)))
urlunquote_plus = allow_lazy(urlunquote_plus, six.text_type)

def urlencode(query, doseq=0):
    """
    A version of Python's urllib.urlencode() function that can operate on
    unicode strings. The parameters are first case to UTF-8 encoded strings and
    then encoded as per normal.
    """
    if isinstance(query, MultiValueDict):
        query = query.lists()
    elif hasattr(query, 'items'):
        query = query.items()
    return urllib_parse.urlencode(
        [(force_str(k),
         [force_str(i) for i in v] if isinstance(v, (list,tuple)) else force_str(v))
            for k, v in query],
        doseq)

def cookie_date(epoch_seconds=None):
    """
    Formats the time to ensure compatibility with Netscape's cookie standard.

    Accepts a floating point number expressed in seconds since the epoch, in
    UTC - such as that outputted by time.time(). If set to None, defaults to
    the current time.

    Outputs a string in the format 'Wdy, DD-Mon-YYYY HH:MM:SS GMT'.
    """
    rfcdate = formatdate(epoch_seconds)
    return '%s-%s-%s GMT' % (rfcdate[:7], rfcdate[8:11], rfcdate[12:25])

def http_date(epoch_seconds=None):
    """
    Formats the time to match the RFC1123 date format as specified by HTTP
    RFC2616 section 3.3.1.

    Accepts a floating point number expressed in seconds since the epoch, in
    UTC - such as that outputted by time.time(). If set to None, defaults to
    the current time.

    Outputs a string in the format 'Wdy, DD Mon YYYY HH:MM:SS GMT'.
    """
    rfcdate = formatdate(epoch_seconds)
    return '%s GMT' % rfcdate[:25]

def parse_http_date(date):
    """
    Parses a date format as specified by HTTP RFC2616 section 3.3.1.

    The three formats allowed by the RFC are accepted, even if only the first
    one is still in widespread use.

    Returns an integer expressed in seconds since the epoch, in UTC.
    """
    # emails.Util.parsedate does the job for RFC1123 dates; unfortunately
    # RFC2616 makes it mandatory to support RFC850 dates too. So we roll
    # our own RFC-compliant parsing.
    for regex in RFC1123_DATE, RFC850_DATE, ASCTIME_DATE:
        m = regex.match(date)
        if m is not None:
            break
    else:
        raise ValueError("%r is not in a valid HTTP date format" % date)
    try:
        year = int(m.group('year'))
        if year < 100:
            if year < 70:
                year += 2000
            else:
                year += 1900
        month = MONTHS.index(m.group('mon').lower()) + 1
        day = int(m.group('day'))
        hour = int(m.group('hour'))
        min = int(m.group('min'))
        sec = int(m.group('sec'))
        result = datetime.datetime(year, month, day, hour, min, sec)
        return calendar.timegm(result.utctimetuple())
    except Exception:
        raise ValueError("%r is not a valid date" % date)

def parse_http_date_safe(date):
    """
    Same as parse_http_date, but returns None if the input is invalid.
    """
    try:
        return parse_http_date(date)
    except Exception:
        pass

# Base 36 functions: useful for generating compact URLs

def base36_to_int(s):
    """
    Converts a base 36 string to an ``int``. Raises ``ValueError` if the
    input won't fit into an int.
    """
    # To prevent overconsumption of server resources, reject any
    # base36 string that is long than 13 base36 digits (13 digits
    # is sufficient to base36-encode any 64-bit integer)
    if len(s) > 13:
        raise ValueError("Base36 input too large")
    value = int(s, 36)
    # ... then do a final check that the value will fit into an int to avoid
    # returning a long (#15067). The long type was removed in Python 3.
    if not six.PY3 and value > sys.maxint:
        raise ValueError("Base36 input too large")
    return value

def int_to_base36(i):
    """
    Converts an integer to a base36 string
    """
    digits = "0123456789abcdefghijklmnopqrstuvwxyz"
    factor = 0
    if i < 0:
        raise ValueError("Negative base36 conversion input.")
    if not six.PY3:
        if not isinstance(i, six.integer_types):
            raise TypeError("Non-integer base36 conversion input.")
        if i > sys.maxint:
            raise ValueError("Base36 conversion input too large.")
    # Find starting factor
    while True:
        factor += 1
        if i < 36 ** factor:
            factor -= 1
            break
    base36 = []
    # Construct base36 representation
    while factor >= 0:
        j = 36 ** factor
        base36.append(digits[i // j])
        i = i % j
        factor -= 1
    return ''.join(base36)

def parse_etags(etag_str):
    """
    Parses a string with one or several etags passed in If-None-Match and
    If-Match headers by the rules in RFC 2616. Returns a list of etags
    without surrounding double quotes (") and unescaped from \<CHAR>.
    """
    etags = ETAG_MATCH.findall(etag_str)
    if not etags:
        # etag_str has wrong format, treat it as an opaque string then
        return [etag_str]
    etags = [e.encode('ascii').decode('unicode_escape') for e in etags]
    return etags

def quote_etag(etag):
    """
    Wraps a string in double quotes escaping contents as necesary.
    """
    return '"%s"' % etag.replace('\\', '\\\\').replace('"', '\\"')

def same_origin(url1, url2):
    """
    Checks if two URLs are 'same-origin'
    """
    p1, p2 = urllib_parse.urlparse(url1), urllib_parse.urlparse(url2)
    return (p1.scheme, p1.hostname, p1.port) == (p2.scheme, p2.hostname, p2.port)

def is_safe_url(url, host=None):
    """
    Return ``True`` if the url is a safe redirection (i.e. it doesn't point to
    a different host).

    Always returns ``False`` on an empty url.
    """
    if not url:
        return False
    netloc = urllib_parse.urlparse(url)[1]
    return not netloc or netloc == host
