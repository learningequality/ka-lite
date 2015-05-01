import cProfile
import os

from time import time, strftime

from kalite.distributed import settings

def profile(filename):
    """ Decorator to profile a function. A no-op if setting PROFILE is False.
    :param filename: A file where the profile stats will be written. Has a %Y-%m-%d-%H-%M-%S timestamp appended to it.
    """
    def _outer_f(func):
        def _inner_f(*args, **kwargs):
            pr = cProfile.Profile()
            pr.enable()
            func(*args, **kwargs)
            pr.disable()
            timestamp = strftime("%Y-%m-%d-%H-%M-%S")
            fn, ext = os.path.splitext(filename)
            pr.dump_stats(fn + timestamp + ext)
        if settings.PROFILE:
            return _inner_f
        else:
            return func
    return _outer_f