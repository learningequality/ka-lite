"""
For functions mucking with internet access
"""
import ifcfg
import os
import platform
import re
import requests
import socket

from urlparse import parse_qs, urlsplit, urlunsplit
from urllib import urlencode


def am_i_online(url, expected_val=None, search_string=None, timeout=5, allow_redirects=True):
    """Test whether we are online or not.
    returns True or False.
    Eats all exceptions!
    """
    assert not (search_string and expected_val is not None), "Search string and expected value cannot both be set"

    from kalite.version import user_agent

    try:
        if not search_string and expected_val is None:
            response = requests.head(url, headers={"user-agent": user_agent()})
        else:
            response = requests.get(url, timeout=timeout, allow_redirects=allow_redirects, headers={"user-agent": user_agent()})

        # Validate that response came from the requested url
        if response.status_code != 200:
            return False
        elif not allow_redirects and response.url != url:
            return False

        # Check the output, if expected values are specified
        if expected_val is not None:
            return expected_val == response.text
        elif search_string:
            return search_string in response.text

        return True

    except Exception as e:
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
