#import decorator
import types
import unittest

from kalite import settings


def x_only(f, cond, msg):
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
        @unittest.skipIf(cond, msg)
        def wrapped_fn(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapped_fn


def distributed_only(f):
    """Run the test only on the distributed server"""
    return x_only(f, not settings.CENTRAL_SERVER, "Distributed server test")


def central_only(f):
    """Run the test only on the central server"""
    return x_only(f, settings.CENTRAL_SERVER, "Central server test")
    
         