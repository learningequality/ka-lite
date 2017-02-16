"""
For functions mucking with internet access
"""
import logging
import os
import platform
import re
import requests
from urllib import urlencode
from urlparse import parse_qs, urlsplit, urlunsplit, urljoin

from django.conf import settings
import ifcfg

from django.core.urlresolvers import reverse
from requests.exceptions import ConnectionError, ReadTimeout


logger = logging.getLogger(__name__)


def am_i_online():
    """Test whether we are online or not.
    returns True or False.
    Eats all exceptions!   <- great :( /benjaoming
    """
    from kalite.version import user_agent

    timeout = 15  # seconds
    url = urljoin(settings.CENTRAL_SERVER_URL, reverse("get_server_info"))

    try:
        # Based on experience, 5 seconds is too little
        response = requests.get(url, timeout=timeout, allow_redirects=False, headers={"user-agent": user_agent()})

        # Validate that response came from the requested url
        if response.status_code != 200:
            
            logger.warning("Unexpected response detecting online status: {}".format(response))
            return False

        return True

    except ReadTimeout:
        logger.info(
            ("Assuming offline status, timeout={} seconds, timed out while "
             "fetching {}").format(timeout, url)
        )
        return False
    except ConnectionError:
        logger.info(
            "Assuming offline status, connection error while fetching {}".format(url)
        )
        return False
    except Exception as e:
        logger.warning("Unhandled exception when detecting if online: {}".format(e))
        return False


def generate_all_paths(path, base_path="/"):
    if not base_path.endswith("/"):   # Must have trailing slash to work.
        base_path += "/"

    if path.endswith("/"):        # Must NOT have trailing slash to work.
        path = path[0:-1]

    all_paths = []
    cur_path = base_path[0:-1]
    for dirname in path[len(base_path) - 1:].split("/"):  # start AFTER the base path
        cur_path += dirname + "/"
        all_paths.append(cur_path)
    return all_paths


def set_query_params(url, param_dict):
    """Given a URL, set or replace a query parameter and return the
    modified URL.

    >>> set_query_params('http://example.com?foo=bar&biz=baz',  {'foo': 'stuff'})
    'http://example.com?foo=stuff&biz=baz'

    modified from http://stackoverflow.com/questions/4293460/how-to-add-custom-parameters-to-an-url-query-string-with-python
    """
    scheme, netloc, path, query_string, fragment = urlsplit(url)
    query_params = parse_qs(query_string, keep_blank_values=True)

    for param_name, param_value in param_dict.items():
        if param_value is None:
            del query_params[param_name]
        else:
            query_params[param_name] = [param_value]

    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def get_ip_addresses(include_loopback=True):
    """Get a list of all the IP addresses for adapters on the local system.

    You can specify to either include the loopback device (127.0.0.1) or not.
    """

    system = platform.system()

    if system.lower() in ["linux", "darwin", "macosx"]:
        # on Linux and OSX, use the ifcfg library to wrap ifconfig
        ips = [iface.get("inet") for iface in ifcfg.interfaces().values()]
    elif system.lower() == "windows":
        # on Windows, run ipconfig and parse the output
        ipconfig = os.popen("ipconfig /all").read()
        ips = [match[1] for match in re.findall("IP(v4)? Address[\.\: ]+([\d\.]+)", ipconfig)]
    else:
        ips = []

    # remove empty values for adapters without an IP
    ips = set(ips) - set([None, ""])

    if include_loopback:
        ips = ips.union(["127.0.0.1"])
    else:
        ips = ips - set(["127.0.0.1"])

    return list(ips)
