"""
For functions mucking with internet access
"""
import logging
import requests

from django.http import HttpResponse
from django.utils import simplejson


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
        logging.getLogger("kalite").debug("am_i_online: %s" % e)
        return False


if __name__=="__main__":
    print am_i_online()