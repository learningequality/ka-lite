# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# callable.py - Callable classes
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2005-2012 Dirk Meyer, Jason Tackaberry, et al.
#
# Please see the file AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------
from __future__ import absolute_import

__all__ = [ 'Callable', 'WeakCallable' ]

# Python imports
import _weakref
import types
import logging
import atexit

# Kaa imports
from .errors import CallableError
from .utils import property

# get logging object
log = logging.getLogger('kaa.base.core.callable')

# Variable that is set to True (via atexit callback) when python interpreter
# is in the process of shutting down.  If we're interested if the interpreter
# is shutting down, we don't want to test that this variable is True, but
# rather that it is not False, because as it is prefixed with an underscore,
# the interpreter might already have deleted this variable in which case it
# is None.
_python_shutting_down = False


def weakref_data(data, destroy_cb = None):
    if type(data) in (str, int, long, types.NoneType, types.FunctionType):
        # Naive optimization for common immutable cases.
        return data
    elif type(data) == types.MethodType:
        cb = WeakCallable(data)
        if destroy_cb:
            cb.weakref_destroyed_cb = destroy_cb
            cb.ignore_caller_args = True
        return cb
    elif type(data) in (list, tuple):
        d = []
        for item in data:
            d.append(weakref_data(item, destroy_cb))
        if type(data) == tuple:
            d = tuple(d)
        return d
    elif type(data) == dict:
        d = {}
        for key, val in data.items():
            d[weakref_data(key)] = weakref_data(val, destroy_cb)
        return d
    else:
        try:
            if destroy_cb:
                return _weakref.ref(data, destroy_cb)
            return _weakref.ref(data)
        except TypeError:
            pass

    return data

def unweakref_data(data):
    if type(data) in (str, int, long, types.NoneType):
        # Naive optimization for common immutable cases.
        return data
    elif type(data) == _weakref.ReferenceType:
        return data()
    elif type(data) == WeakCallable:
        return data._get_func()
    elif type(data) in (list, tuple):
        d = []
        for item in data:
            d.append(unweakref_data(item))
        if type(data) == tuple:
            d = tuple(d)
        return d
    elif type(data) == dict:
        d = {}
        for key, val in data.items():
            d[unweakref_data(key)] = unweakref_data(val)
        return d
    else:
        return data


class Callable(object):
    """
    Wraps an existing callable, binding to it any given args and kwargs.

    When the Callable object is invoked, the arguments passed on invocation
    are combined with the arguments specified at construction time and the
    underlying callable is invoked with those arguments.
    """
    def __init__(self, func, *args, **kwargs):
        """
        :param func: callable function or object
        :param args: arguments to be passed to func when invoked
        :param kwargs: keyword arguments to be passed to func when invoked
        """
        super(Callable, self).__init__()
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._ignore_caller_args = False
        self._init_args_first = False


    @property
    def ignore_caller_args(self):
        """
        If True, any arguments passed when invoking the Callable object are not
        passed to the underlying callable.

        Default value is False, so all arguments are passed to the callable.
        """
        return self._ignore_caller_args

    @ignore_caller_args.setter
    def ignore_caller_args(self, value):
        self._ignore_caller_args = value


    @property
    def init_args_first(self):
        """
        If True, any arguments passed upon invocation of the Callable object take
        precedence over those arguments passed at object initialization time.
        e.g. ``func(constructor_args..., invocation_args...)``

        Default value is False, so invocation arguments take precedence over init
        arguments. e.g. ``func(invocation_args..., constructor_args...)``

        "A takes precedence over B" means that non-keyword arguments are passed
        in order of A + B, and keyword arguments from A override same-named keyword
        arguments from B.
        """
        return self._init_args_first

    @init_args_first.setter
    def init_args_first(self, value):
        self._init_args_first = value


    @property
    def user_args_first(self):
        log.warning('user_args_first is deprecated; use init_args_first')
        return self._init_args_first

    @user_args_first.setter
    def user_args_first(self, value):
        log.warning('user_args_first is deprecated; use init_args_first')
        self._init_args_first = value


    def _get_init_args(self):
        """
        Return the arguments provided by the user on __init__.
        """
        return self._args, self._kwargs


    def _get_func(self):
        return self._func


    def _merge_args(self, args, kwargs, init_args=None, init_kwargs=None):
        if init_args is None:
            # We don't use _get_init_args() here to avoid the extra function
            # call, even though it would make WeakCallable implementation
            # slightly more elegant.  WeakCallable overrides _merge_args
            # instead.
            init_args, init_kwargs = self._args, self._kwargs

        if self._ignore_caller_args:
            return init_args, init_kwargs
        else:
            # Fast paths.
            if not args and not kwargs:
                return init_args, init_kwargs
            elif not init_args and not init_kwargs:
                return args, kwargs

            # Slower paths, where we must copy kwargs in order to merge user
            # kwargs and invocation-time kwargs.
            if self._init_args_first:
                cb_args, cb_kwargs = init_args + args, kwargs.copy()
                cb_kwargs.update(init_kwargs)
            else:
                cb_args, cb_kwargs = args + init_args, init_kwargs.copy()
                cb_kwargs.update(kwargs)

        return cb_args, cb_kwargs


    def __call__(self, *args, **kwargs):
        """
        Invoke the callable.

        The arguments passed here take precedence over constructor arguments
        if the :attr:`~kaa.Callable.init_args_first` property is False (default).
        The wrapped callable's return value is returned.
        """
        cb = self._get_func()
        if cb is None:
            raise CallableError('attempting to invoke an invalid callable')

        cb_args, cb_kwargs = self._merge_args(args, kwargs)
        return cb(*cb_args, **cb_kwargs)


    def __repr__(self):
        """
        Convert to string for debug.
        """
        return '<%s for %s>' % (self.__class__.__name__, self._func)


    def __eq__(self, func):
        """
        Compares the given function with the function we're wrapping.
        """
        return id(self) == id(func) or self._get_func() == func


class WeakCallable(Callable):
    """
    Weak variant of the Callable class.  Only weak references are held for
    non-intrinsic types (i.e. any user-defined object).

    If the callable is a method, only a weak reference is kept to the instance
    to which that method belongs, and only weak references are kept to any of
    the arguments and keyword arguments.

    This also works recursively, so if there are nested data structures, for example 
    ``kwarg=[1, [2, [3, my_object]]]``, only a weak reference is held for my_object.
    """

    def __init__(self, func, *args, **kwargs):
        super(WeakCallable, self).__init__(func, *args, **kwargs)
        if type(func) == types.MethodType:
            # We can't a weakref of the bound method, since it will probably
            # go dead as soon as this function exists (assuming the caller
            # did WeakCallable(foo.bar)).  Instead we take a weakref of
            # the instance itself, and keep track of the method name.  This
            # assumes the method keeps the same attribute name inside the
            # instance, which is usually true.
            #
            # Fetch the instance of this bound method object.  __self__
            # works on Python 2.6+ and im_self is for Python 2.5.
            instance = getattr(func, '__self__', getattr(func, 'im_self', None))
            self._instance = _weakref.ref(instance, self._weakref_destroyed)
            self._func = func.__name__
        else:
            self._instance = None
            # Don't weakref lambdas.
            if getattr(func, '__name__', None) != '<lambda>':
                self._func = _weakref.ref(func, self._weakref_destroyed)

        self._args = weakref_data(args, self._weakref_destroyed)
        self._kwargs = weakref_data(kwargs, self._weakref_destroyed)
        self._weakref_destroyed_user_cb = None


    def __repr__(self):
        if self._instance and self._instance():
            name = "method %s of %s" % (self._func, self._instance())
        else:
            name = self._func
        return '<%s for %s>' % (self.__class__.__name__, name)

    def _get_func(self):
        if self._instance:
            if self._instance() != None:
                return getattr(self._instance(), self._func)
        elif isinstance(self._func, _weakref.ReferenceType):
            return self._func()
        else:
            return self._func


    def _get_init_args(self):
        # Needed by Signal.disconnect()
        return unweakref_data(self._args), unweakref_data(self._kwargs)


    def _merge_args(self, args, kwargs, init_args=None, init_kwargs=None):
        init_args, init_kwargs = unweakref_data(self._args), unweakref_data(self._kwargs)
        return super(WeakCallable, self)._merge_args(args, kwargs, init_args, init_kwargs)


    def __call__(self, *args, **kwargs):
        if _python_shutting_down != False:
            # Shutdown
            return False

        return super(WeakCallable, self).__call__(*args, **kwargs)


    @property
    def weakref_destroyed_cb(self):
        """
        A callback that's invoked when any of the weak references held (either
        for the callable or any of the arguments passed on the constructor)
        become dead.

        When this happens, the Callable is invalid and any attempt to invoke
        it will raise a kaa.CallableError.

        The callback is passed the weakref object (which is probably dead).
        If the callback requires additional arguments, they can be encapsulated
        in a :class:`kaa.Callable` object.
        """
        return self._weakref_destroyed_user_cb

    @weakref_destroyed_cb.setter
    def weakref_destroyed_cb(self, callback):
        if not callable(callback):
            raise ValueError('Value must be callable')
        self._weakref_destroyed_user_cb = callback


    def _weakref_destroyed(self, object):
        if _python_shutting_down != False:
            # Shutdown
            return
        try:
            if self._weakref_destroyed_user_cb:
                return self._weakref_destroyed_user_cb(object)
        except Exception:
            log.exception("Exception raised during weakref destroyed callback")
        finally:
            # One of the weak refs has died, consider this WeakCallable invalid.
            self._instance = self._func = None



def _shutdown_weakref_destroyed():
    global _python_shutting_down
    _python_shutting_down = True

atexit.register(_shutdown_weakref_destroyed)
