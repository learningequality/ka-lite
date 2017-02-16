from urlparse import urlparse, urlunparse
from django.http import QueryDict

def get_request_ip(request):
    """Return the IP address from a HTTP request object."""
    return request.META.get("HTTP_X_FORWARDED_FOR") \
        or request.META.get("REMOTE_ADDR") \
        or request.META.get("HTTP_X_REAL_IP")  # set by some proxies


def is_loopback_connection(request):
    """Test whether the IP making the request is the same as the IP serving the request.
    """
    # get the external IP address of the local host
    host_ip = socket.gethostbyname(socket.gethostname())

    # get the remote (browser) device's IP address (checking extra headers first in case we're behind a proxy)
    remote_ip = get_request_ip(request)

    # if the requester's IP is either localhost or the same as the server's IP, then it's a loopback
    return remote_ip in ["127.0.0.1", "localhost", host_ip]
