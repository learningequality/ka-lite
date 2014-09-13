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
