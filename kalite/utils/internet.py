"""
For functions mucking with internet access
"""
import logging
import requests
import socket

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


def is_loopback_connection(request):
    """ Test whether the IP making the request is the same as the IP serving the request. """
    try:
        host = request.META.get("HTTP_HOST", "127.0.0.1")
        host_ip = socket.gethostbyaddr(host.split(":")[0])[2][0]
        return request.META.get("REMOTE_ADDR") in ["127.0.0.1", host_ip]
    except:
        return False

if __name__=="__main__":
    print am_i_online()
    