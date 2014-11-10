import logging
import warnings


def deprecated(func):
    '''
    Signals in stdout if we're using a deprecated function.
    '''
    def new_func(*args, **kwargs):
        warnings.warn("Call to deprecated function {0}.".format(func.__name__),
                      category=DeprecationWarning)
        return func(*args, **kwargs)

    new_func.__name__ = func.__name__
    new_func.__doc__ = func.__doc__
    new_func.__dict__.update(func.__dict__)
    return new_func


def logging_silenced(func=None):

    if func:
        def func_with_logging_silenced(*args, **kwargs):
            with logging_silenced:
                return func(*args, **kwargs)

        return func_with_logging_silenced


def _silence_logging_enter():
    print 'entered'
    logging.disable(logging.CRITICAL)


def _silence_logging_exit(exc_type, exc_value, traceback):
    logging.disable(logging.NOTSET)


logging_silenced.__enter__ = _silence_logging_enter
logging_silenced.__exit__ = _silence_logging_exit
