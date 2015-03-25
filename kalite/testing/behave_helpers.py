"""
These methods will probably be used again and again in behave tests.
We'll make a few assumptions: every function here takes a behave context
as the first positional argument, and should assert what it expects from 
that context in order to function (instead of just silently failing).
"""
import httplib
import json

from django.contrib.auth.models import User

def check_test_server_url(f):
    """ A decorator to ensure we have minimal capabilites -- i.e. a live_server_url to use.
    """
    def new_f(context, *args, **kwargs):
        assert hasattr(context, "hijacked_test_case"), "The context needs a hijacked_test_case for this helper."
        assert hasattr(context.hijacked_test_case, "live_server_url"), "context.hijacked_test_case needs attribute live_server_url for this helper"
        f(context, *args, **kwargs)

    return new_f


def login_as_admin(context, admin_name="admin", admin_pass="abc123"):
    # Create the user if it doesn't exist
    if not User.objects.filter(username=admin_name):
        u = User(username=admin_name, password=admin_pass)
        u.save()
    data = json.dumps({"username": admin_name, "password": admin_pass})
    # TODO(MCGallaspy): Once there's a RESTful way to login put it here
    # post(context, "/securesync/login", data)


def logout(context):
    # TODO(MCGallaspy): Once there's a RESTful way to logout put it here
    # get(context, "/securesync/logout")
    pass


def post(context, url, data=""):
    """ Sends a POST request to the testing server associated with context
    
    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    data: A string containing the body of the request

    Returns the response.
    """
    return request(context, url, method="POST", data=data)


def get(context, url, data=""):
    """ Sends a GET request to the testing server associated with context
    
    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    data: A string containing the body of the request

    Returns the response.
    """
    return request(context, url, method="GET", data=data)



@check_test_server_url
def request(context, url, method="GET", data=""):
    """ Make a request to the testing server associated with context

    context: A `behave` context
    url: A relative url, i.e. "/zone/management/None" or "/securesync/logout"
    method: The HTTP method to use, i.e. GET, POST
    data: A string containing the body of the request

    Returns the response.
    """
    # cut off the "http://" part
    lsurl = context.hijacked_test_case.live_server_url[7:]
    conn = httplib.HTTPConnection(lsurl)
    conn.request(method, url, data)
    resp = conn.getresponse()
    conn.close()
    return resp
