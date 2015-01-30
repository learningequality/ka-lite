import urllib
import urlparse


def sort_string(s):
    """A simple little toy to sort a string."""
    return ''.join(sorted(list(s))) if s else s


def sort_string_key():
    """Returns a key function that produces a key by sorting a string."""
    return sort_string


def filter_query_params(url, remove_params):
    """
    Remove all provided parameters from the query section of the ``url``.

    :param remove_params: A list of (param, newvalue) to scrub from the URL.
    :type remove_params: list
    """
    if not url:
        return url

    remove_params = dict((p, None) if isinstance(p, basestring) else p
        for p in remove_params)

    parsed_url = urlparse.urlparse(url)
    parsed_qsl = urlparse.parse_qsl(parsed_url.query, keep_blank_values=True)

    filtered_qsl = [(p, remove_params.get(p, v)) for p, v in parsed_qsl]
    filtered_qsl = [(p, v) for p, v in filtered_qsl if v is not None]

    filtered_url = urlparse.ParseResult(
        scheme=parsed_url.scheme,
        netloc=parsed_url.netloc,
        path=parsed_url.path,
        params=parsed_url.params,
        query=urllib.urlencode(filtered_qsl),
        fragment=parsed_url.fragment)

    return urlparse.urlunparse(filtered_url)


def filter_query_params_key(remove_params):
    """
    Returns a key function that produces a key by removing params from a URL.

    :param remove_params: A list of query params to scrub from provided URLs.
    :type remove_params: list
    """
    def filter(url):
        return filter_query_params(url, remove_params)
    return filter


def filter_headers(headers, remove_headers):
    """
    Remove undesired headers from the provided ``headers`` dict.
    The header keys are case-insensitive.

    :param remove_headers: A list of header names to remove or redact.
    :type remove_headers: list
    """
    # Upgrade bare 'header' to ('header', None) in remove_headers
    remove_headers = [(h, None) if isinstance(h, basestring) else h
        for h in remove_headers]

    # Make remove_headers a dict with lower-cased keys
    remove_headers = dict((h.lower(), v) for h, v in remove_headers)

    # Replace values in headers with values from remove_headers
    headers = dict((h, remove_headers.get(h.lower(), v))
        for h, v in headers.items())

    # Remove any that ended up None
    headers = dict((h, v) for h, v in headers.items() if v is not None)
    return headers


def filter_headers_key(remove_headers):
    """
    Returns a key function that produces a key by removing headers from a dict.

    :param remove_headers: A list of header names to remove.
    :type remove_headers: list
    """
    def filter(headers):
        return filter_headers(headers, remove_headers)
    return filter
