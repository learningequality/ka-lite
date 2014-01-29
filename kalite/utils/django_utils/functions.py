from urlparse import urlparse, urlunparse
from django.http import QueryDict

def get_request_ip(request):
    """Return the IP address from a HTTP request object."""
    return request.META.get("HTTP_X_FORWARDED_FOR") \
        or request.META.get("REMOTE_ADDR") \
        or request.META.get("HTTP_X_REAL_IP")  # set by some proxies

def set_query_param(url, attr, val):
    """
    Taken from http://stackoverflow.com/questions/5755150/altering-one-query-parameter-in-a-url-django
    """
    (scheme, netloc, path, params, query, fragment) = urlparse(url)
    query_dict = QueryDict(query).copy()
    query_dict[attr] = val
    query = query_dict.urlencode()
    return urlunparse((scheme, netloc, path, params, query, fragment))