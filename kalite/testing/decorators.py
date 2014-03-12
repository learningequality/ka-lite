#import decorator
import types
import unittest

from kalite import settings


def x_server_test(f, cond, msg):
    """Decorator to label test classes or instance methods as x_only,
    x = "main" or "central"
    """

    # taken from unittest.skip
    if isinstance(f, (type, types.ClassType)):
        if not cond:
            f.__unittest_skip__ = True
            f.__unittest_skip_why__ = msg
        return f

    else:
        @unittest.skipIf(not cond, msg)
        def wrapped_fn(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_fn


def distributed_server_test(f):
    """Run the test only on the distributed server"""
    return x_server_test(f, not settings.CENTRAL_SERVER, "Distributed server test")


def central_server_test(f):
    """Run the test only on the central server"""
    return x_server_test(f, settings.CENTRAL_SERVER, "Central server test")


def allow_api_profiling(handler):
    """
    For API requests decorated with this decorator,
    if 'debug' is passed in with DEBUG=True,
    it will add a BODY tag to the json response--allowing
    the debug_toolbar to be used.
    """
    if not settings.DEBUG:
        # for efficiency reasons, just return the API function when not in DEBUG mode.
        return handler
    else:
        def aap_wrapper_fn(request, *args, **kwargs):
            response = handler(request, *args, **kwargs)
            if not request.is_ajax() and response["Content-Type"] == "application/json":
                # Add the "body" tag, which allows the debug_toolbar to attach
                response.content = "<body>%s</body>" % response.content
                response["Content-Type"] = "text/html"
            return response
        return aap_wrapper_fn
