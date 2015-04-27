# -*- coding: utf8 -*-
# -----------------------------------------------------------------------------
# errors.py - exception classes used by the kaa core
# -----------------------------------------------------------------------------
# It is not possible to LazyProxy exception classes, so custom exceptions used
# by any of the core modules which are lazy-loaded are contained in this module
# which is imported immediately when kaa is imported.
#
# Exceptions outside the core modules (e.g. kaa.db, kaa.rpc) are defined within
# their respective modules.
# -----------------------------------------------------------------------------
# kaa The Kaa Application Framework
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

import traceback

__all__ = [
    'make_exception_class', 'CallableError', 'AsyncExceptionBase', 'AsyncException',
    'TimeoutException', 'InProgressAborted', 'SocketError'
]

def make_exception_class(name, bases, dict):
    """
    Class generator for AsyncException.  Creates AsyncException class
    which derives the class of a particular Exception instance.
    """
    def create(exc, stack, *args):
        return type(name, bases + (exc.__class__,), {})(exc, stack, *args)
    return create


class CallableError(Exception):
    pass


class AsyncExceptionBase(Exception):
    """
    Base class for asynchronous exceptions.  This class can be used to raise
    exceptions where the traceback object is not available.  The stack is
    stored (which is safe to reference and can be pickled) instead, and when
    AsyncExceptionBase instances are printed, the original traceback will
    be printed.

    This class will proxy the given exception object.
    """
    def __init__(self, exc, stack, *args):
        self._kaa_exc = exc
        self._kaa_exc_stack = stack
        self._kaa_exc_args = args

    def __getattribute__(self, attr):
        # Used by python 2.5, where exceptions are new-style classes.
        if attr.startswith('_kaa'):
            return super(AsyncExceptionBase, self).__getattribute__(attr)
        return getattr(self._kaa_exc, attr)

    def __getattr__(self, attr):
        # Used by python 2.4, where exceptions are old-style classes.
        exc = self._kaa_exc
        if attr == '__members__':
            return [ x for x in dir(exc) if not callable(getattr(exc, x)) ]
        elif attr == '__methods__':
            return [ x for x in dir(exc) if callable(getattr(exc, x)) ]
        return self.__getattribute__(attr)

    def _kaa_get_header(self):
        return 'Exception raised asynchronously; traceback follows:'

    def __str__(self):
        dump = ''.join(traceback.format_list(self._kaa_exc_stack))
        info = '%s: %s' % (self._kaa_exc.__class__.__name__, str(self._kaa_exc))
        return self._kaa_get_header() + '\n' + dump + info


class AsyncException(AsyncExceptionBase):
    __metaclass__ = make_exception_class


class InProgressAborted(BaseException):
    """
    This exception is thrown into an InProgress object when 
    :meth:`~kaa.InProgress.abort` is called.

    For :class:`~kaa.ThreadCallable` and  :class:`~kaa.ThreadPoolCallable`
    this exception is raised inside the threaded callable.  This makes it
    potentially an asynchronous exception (when used this way), and therefore
    it subclasses BaseException, similar in rationale to KeyboardInterrupt
    and SystemExit, and also (for slightly different reasons) GeneratorExit,
    which as of Python 2.6 also subclasses BaseException.
    """
    def __init__(self, *args, **kwargs):
        super(InProgressAborted, self).__init__(*args)
        self.message = args[0] if args else None
        self.inprogress = kwargs.get('inprogress')
        self.origin = kwargs.get('origin')

    def __inprogress__(self):
        # Support kaa.inprogress(exc)
        return self.inprogress


class TimeoutException(InProgressAborted):
    """
    This exception is raised by an :class:`~kaa.InProgress` returned by
    :meth:`~kaa.InProgress.timeout` when the timeout occurs.

    For example::

        sock = kaa.Socket()
        try:
            yield sock.connect('deadhost.com:80').timeout(10)
        except kaa.TimeoutException:
            print 'Connection timed out after 10 seconds'
    """
    pass


class SocketError(Exception):
    pass
