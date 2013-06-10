"""
For functions mucking with internet access
"""
import logging
import requests

def am_i_online(url="http://google.com/", expected_val=None, timeout=5):
    """Test whether we are online or not.
    returns True or False.  
    Eats all exceptions!
    """
    
    try:
        if expected_val is not None:
            return expected_val == requests.get(url, timeout=timeout)
        else:
            return requests.head(url).status_code==200
    except Exception as e:
        logging.getLogger("kalite").debug("am_i_online: %s" % str(e))
        return False


if __name__=="__main__":
    print am_i_online()