from urlparse import urlparse, urlunparse
from django.http import QueryDict

def get_request_ip(request):
    """Return the IP address from a HTTP request object."""
    return request.META.get("HTTP_X_FORWARDED_FOR") \
        or request.META.get("REMOTE_ADDR") \
        or request.META.get("HTTP_X_REAL_IP")  # set by some proxies
