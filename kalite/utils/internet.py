"""
For functions mucking with internet access
"""
import os
import requests
from urlparse import parse_qs, urlsplit, urlunsplit
from urllib import urlencode


from django.http import HttpResponse
from django.utils import simplejson

from settings import LOG as logging


class StatusException(Exception):
    """Class used for turning a HTTP response error into an exception"""
    def __init__(self, message, status_code):
        super(StatusException, self).__init__(message)
        self.args = (status_code,)
        self.status_code = status_code
        
class JsonResponse(HttpResponse):
    """Wrapper class for generating a HTTP response with JSON data"""
    def __init__(self, content, *args, **kwargs):
        if not isinstance(content, str) and not isinstance(content, unicode):
            content = simplejson.dumps(content, ensure_ascii=False)
        super(JsonResponse, self).__init__(content, content_type='application/json', *args, **kwargs)

    
def am_i_online(url, expected_val=None, search_string=None, timeout=5, allow_redirects=True):
    """Test whether we are online or not.
    returns True or False.  
    Eats all exceptions!
    """
    assert not (search_string and expected_val is not None), "Search string and expected value cannot both be set"

    try:
        if not search_string and expected_val is None:
            response = requests.head(url)
        else:
            response = requests.get(url, timeout=timeout, allow_redirects=allow_redirects)

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
        logging.debug("am_i_online: %s" % e)
        return False



def generate_all_paths(path, base_path="/"):

    if not base_path.endswith("/"):   # Must have trailing slash to work.
        base_path += "/"
        
    if not path.endswith("/"):        # Must NOT have trailing slash to work.
        path = path[0:-1]
        
    all_paths = []
    cur_path = base_path[0:-1]
    for dirname in path[len(base_path)-1:].split("/"): # start AFTER the base path
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
    query_params = parse_qs(query_string)

    for param_name, param_value in param_dict.items():
        query_params[param_name] = [param_value]
    new_query_string = urlencode(query_params, doseq=True)

    return urlunsplit((scheme, netloc, path, new_query_string, fragment))


def is_sibling(path1, path2):
    return os.path.dirname(path1) == os.path.dirname(path2)


if __name__ == "__main__":
    print generate_all_paths("/test/me/out")
    print generate_all_paths("/test/me/out/")
    print generate_all_paths("/test/me/out", base_path="/test")
    
    print am_i_online()