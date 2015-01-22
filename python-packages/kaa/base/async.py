# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# async.py - Async callback handling (InProgress)
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2006-2012 Dirk Meyer, Jason Tackaberry, et al.
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

__all__ = [
    'InProgress', 'InProgressCallable', 'InProgressAny', 'InProgressAll', 'inprogress',
    'InProgressStatus', 'FINISH_RESULT', 'FINISH_SELF', 'FINISH_IDX_RESULT'
]

# python imports
import sys
import logging
import traceback
import time
import _weakref
import threading
import types

# kaa.base imports
from .errors import AsyncException, AsyncExceptionBase, InProgressAborted, TimeoutException
from .utils import property
from .callable import Callable
from .core import Object, Signal, Signals, CoreThreading

# get logging object
log = logging.getLogger('kaa.base.core.async')

# Constants for how InProgressAny/All are finished
FINISH_IDX = 'FINISH_IDX'
FINISH_RESULT = 'FINISH_RESULT'
FINISH_SELF = 'FINISH_SELF'
FINISH_IDX_RESULT = 'FINISH_IDX_RESULT'

# A set of weakrefs for all InProgress objects that have unhandled
# exceptions.  We need to keep global references to the weakrefs in
# case the weakref attached to the InProgress gets deleted before the
# InProgress itself does, in which case the log callback would never
# get called.
_unhandled_exceptions = set()


def inprogress(obj):
    """
    Returns a suitable :class:`~kaa.InProgress` for the given object.

    :param obj: object to represent as an InProgress.
    :return: an :class:`~kaa.InProgress` representing ``obj``

    The precise behaviour of an object represented as an
    :class:`~kaa.InProgress` should be defined in the documentation for the
    class.  For example, the :class:`~kaa.InProgress` for a
    :class:`~kaa.Process` object will be finished when the process is
    terminated.

    This function simply calls ``__inprogress__()`` of the given ``obj`` if one
    exists, and if not will raise an exception.  In this sense, it behaves
    quite similar to ``len()`` and ``__len__()``.

    It is safe to call this function on InProgress objects.  (The InProgress
    object given will simply be returned.)

    """
    try:
        return obj.__inprogress__()
    except AttributeError:
        raise TypeError("object of type '%s' has no __inprogress__()" % obj.__class__.__name__)



class InProgressStatus(Signal):
    """
    Generic progress status object for InProgress. This object can be
    used as 'progress' member of an InProgress object and the caller
    can monitor the progress.
    """
    def __init__(self, max=0):
        super(InProgressStatus, self).__init__()
        self.start_time = time.time()
        self.pos = 0
        self.max = max
        self._speed = None


    def set(self, pos=None, max=None, speed=None):
        """
        Set new status. The new status is pos of max.
        """
        if max is not None:
            self.max = max
        if pos is not None:
            self.pos = pos
        if pos > self.max:
            self.max = pos
        self._speed = speed
        self.emit(self)


    def update(self, diff=1, speed=None):
        """
        Update position by the given difference.
        """
        self.set(self.pos + diff, speed=speed)


    def get_progressbar(self, width=70):
        """
        Return a small ASCII art progressbar.
        """
        n = 0
        if self.max:
            n = int((self.pos / float(self.max)) * (width-3))
        s = '|%%%ss|' % (width-2)
        return s % ("="*n + ">").ljust(width-2)

    @property
    def elapsed(self):
        """
        Return time elapsed since the operation started.
        """
        return time.time() - self.start_time

    @property
    def eta(self):
        """
        Estimated time left to complete the operation. Depends on the
        operation itself if this is correct or not.
        """
        if not self.pos:
            return 0
        sec = (time.time() - self.start_time) / self.pos
        # we assume every step takes the same amount of time
        return sec * (self.max - self.pos)

    @property
    def percentage(self):
        """
        Return percentage of steps done.
        """
        if self.max:
            return (self.pos * 100.0) / self.max
        return 0

    @property
    def speed(self):
        """
        The current speed of the operation as set by :meth:`set` or
        :meth:`update`.

        This value has no predefined meaning.  It is up to the API to define
        what units this value indicates.
        """
        return self._speed


class InProgress(Signal, Object):
    """
    InProgress objects are returned from functions that require more time to
    complete (because they are either blocked on some resource, are executing
    in a thread, or perhaps simply because they yielded control back to the main
    loop as a form of cooperative time slicing).

    InProgress subclasses :class:`~kaa.Signal`, which means InProgress objects are
    themselves signals.  Callbacks connected to an InProgress receive a single
    argument containing the result of the asynchronously executed task.

    If the asynchronous task raises an exception, the
    :attr:`~kaa.InProgress.exception` member, which is a separate signal, is
    emitted instead.
    """
    __kaasignals__ = {
        'abort':
            '''
            Emitted when abort() is called.

            .. describe:: def callback(exc)

               :param exc: an exception object the InProgress was aborted with.
               :type exc: :class:`~kaa.InProgressAborted`

            If the task cannot be aborted, the callback can return False, which
            will cause an exception to be raised by abort().
            '''
    }

    # Class-wide lock for the rarely-used finished event.  This is a small
    # optimization, saving about 7% of total instance creation time.  See
    # _finished_event_poke() for more details.
    _finished_event_lock = threading.Lock()

    def __init__(self, abortable=None, frame=0):
        """
        :param abortable: see the :attr:`~kaa.InProgress.abortable` property.
        :type abortable: bool
        """
        super(InProgress, self).__init__()
        self._exception_signal = Signal()
        self._finished = False
        self._finished_event = None
        self._exception = None
        self._unhandled_exception = None
        # TODO: make progress a property so we can document it.
        self.progress = None
        # True: always abortable, False: never abortable, None: abortable if
        # 'abort' signal has callbacks
        self._abortable = abortable

        # If debugging is enabled, get the stack frame for the caller who is
        # creating us.  We only do this for DEBUG or more verbose because it
        # involves a slew of stat() calls and other overhead.
        # XXX: getEffectiveLevel() involves walking up the logger hierarchy
        # and is another area of optimization.
        if log.getEffectiveLevel() <= logging.DEBUG:
            self._stack = traceback.extract_stack()[:frame-1]
        else:
            self._stack = None
        self._name = None


    def __repr__(self):
        if not self._name:
            # Go no further than 2 frames up for the owner.  TODO: could
            # use a more intelligent heuristic to determine IP owner.
            if self._stack:
                frame = self._stack[-min(len(self._stack), 2)]
                self._name = ', owner=%s:%d:%s()' % frame[:3]
            else:
                self._name = ''
        finished = 'finished' if self.finished else 'not finished'
        return '<%s object (%s) at 0x%08x%s>' % (self.__class__.__name__, finished, id(self), self._name)


    def __inprogress__(self):
        """
        We subclass Signal which implements this method, but as we are already
        an InProgress, we simply return self.
        """
        return self

    @property
    def exception(self):
        """
        A :class:`~kaa.Signal` emitted when the asynchronous task this InProgress
        represents has raised an exception.

        Callbacks connected to this signal receive three arguments: exception class,
        exception instance, traceback.
        """
        return self._exception_signal


    @property
    def finished(self):
        """
        True if the InProgress is finished.
        """
        return self._finished


    @property
    def result(self):
        """
        The result the InProgress was finished with.  If an exception was thrown
        to the InProgress, accessing this property will raise that exception.
        """
        if not self._finished:
            raise RuntimeError('operation not finished')
        if self._exception:
            # _unhandled_exception could be True if the InProgress exception
            # is being handled synchronously (via the exception callback).  So
            # check that it's actually a weakref instance before trying to
            # remove it from the global unhandled exceptions set.
            if isinstance(self._unhandled_exception, _weakref.ref):
                _unhandled_exceptions.remove(self._unhandled_exception)
                self._unhandled_exception = None
            if self._exception[2]:
                # We have the traceback, so we can raise using it.
                exc_type, exc_value, exc_tb_or_stack = self._exception
                raise exc_type, exc_value, exc_tb_or_stack
            else:
                # No traceback, so construct an AsyncException based on the
                # stack.
                raise self._exception[1]

        return self._result


    @property
    def failed(self):
        """
        True if an exception was thrown to the InProgress, False if it was
        finished without error or if it is not yet finished.
        """
        return bool(self._exception)


    # XXX: is this property sane after all?  Maybe there is no such case where
    # an IP can be just ignored upon abort().  kaa.delay() turned out not to be
    # an example after all.
    @property
    def abortable(self):
        """
        True if the asynchronous task this InProgress represents can be
        aborted by a call to :meth:`~kaa.InProgress.abort`.

        By default :meth:`~kaa.InProgress.abort` will fail if there are no
        callbacks attached to the :attr:`~kaa.InProgress.signals.abort` signal.
        This property may be explicitly set to ``True``, in which case
        :meth:`~kaa.InProgress.abort` will succeed regardless.  An InProgress is
        therefore abortable if the ``abortable`` property has been explicitly
        set to True, or if there are callbacks connected to the
        :attr:`~kaa.InProgress.signals.abort` signal.

        This is useful when constructing an InProgress object that corresponds
        to an asynchronous task that can be safely aborted with no explicit action.
        """
        return self._abortable or (self._abortable is None and self.signals['abort'].count() > 0)


    @abortable.setter
    def abortable(self, abortable):
        self._abortable = abortable


    def _finished_event_poke(self, **kwargs):
        """
        The finished event is used only when the main loop is currently running
        and wait() is called in a different thread than the main loop.

        This function provides an interface for a thread to create the finished
        event on-demand before waiting on it, or for finish() and throw() to
        test if the finished event exists before setting it.

        Because we're doing a test-and-create we need a mutex, and because this
        is not a common operation, we avoid the (roughly 7%) overhead of
        a per-instance lock.  It means that all instances will synchronize on
        this mutex but because it's so rarely accessed from multiple threads I
        doubt there will be any contention on the lock.
        """
        if kwargs.get('set'):
            with self._finished_event_lock:
                self._finished = True
                if self._finished_event:
                    self._finished_event.set()
        elif 'wait' in kwargs:
            with self._finished_event_lock:
                if self._finished:
                    # Nothing to wait on, we're already done.
                    return
                if not self._finished_event:
                    self._finished_event = threading.Event()
            self._finished_event.wait(kwargs['wait'])


    def finish(self, result):
        """
        This method should be called when the owner (creator) of the InProgress is
        finished successfully (with no exception).

        Any callbacks connected to the InProgress will then be emitted with the
        result passed to this method.

        If *result* is an unfinished InProgress, then instead of finishing, we
        wait for the result to finish via :meth:`waitfor`.

        :param result: the result of the completed asynchronous task.  (This can
                       be thought of as the return value of the task if it had
                       been executed synchronously.)
        :return: This method returns self, which makes it convenient to prime InProgress
                 objects with a finished value. e.g. ``return InProgress().finish(42)``
        """
        if self._finished:
            raise RuntimeError('%s already finished' % self)
        if isinstance(result, InProgress) and result is not self:
            # we are still not finished, wait for this new InProgress
            self.waitfor(result)
            return self

        # store result
        self._result = result
        self._exception = None
        # Wake any threads waiting on us
        self._finished_event_poke(set=True)

        # emit signal
        self.emit_when_handled(result)
        # cleanup
        self.disconnect_all()
        self._exception_signal.disconnect_all()
        self.signals['abort'].disconnect_all()
        return self


    def throw(self, type=None, value=None, tb=None, aborted=False):
        """
        This method should be called when the owner (creator) of the InProgress is
        finished because it raised an exception.

        Any callbacks connected to the :attr:`~kaa.InProgress.exception` signal will
        then be emitted with the arguments passed to this method.

        The parameters correspond to sys.exc_info().  If they are not specified
        then the current exception in sys.exc_info() will be used; this is
        analogous to a naked ``raise`` within an ``except`` block.

        .. note::
           Exceptions thrown to InProgress objects that aren't explicitly
           handled will be logged at the INFO level (using a logger name with
           a ``kaa.`` prefix.)  *When* the unhandled asynchronous exception is
           logged depends on the version of Python used.

           Some versions of CPython (e.g 2.6) will log the unhandled exception
           immediately when the InProgress has no more references, while
           others (e.g. 2.7 and 3.2) will only be logged on the next garbage
           collection.


        :param type: the class of the exception
        :param value: the instance of the exception
        :param tb: the traceback object representing where the exception took place
        """
        # This function must deal with a tricky problem.  See:
        # http://mail.python.org/pipermail/python-dev/2005-September/056091.html
        #
        # Ideally, we want to store the traceback object so we can defer the
        # exception handling until some later time.  The problem is that by
        # storing the traceback, we create some ridiculously deep circular
        # references.
        #
        # The way we deal with this is to pass along the traceback object to
        # any handler that can handle the exception immediately, and then
        # discard the traceback.  A stringified formatted traceback is attached
        # to the exception in the formatted_traceback attribute.
        #
        # The above URL suggests a possible non-trivial workaround: create a
        # custom traceback object in C code that preserves the parts of the
        # stack frames needed for printing tracebacks, but discarding objects
        # that would create circular references.  This might be a TODO.
        if type is None:
            type, value, tb = sys.exc_info()
            if value is None:
                raise ValueError('throw() with no parameters but there is no current exception')
        self._exception = type, value, tb
        self._unhandled_exception = True
        stack = traceback.extract_tb(tb)

        # Attach a stringified traceback to the exception object.  Right now,
        # this is the best we can do for asynchronous handlers.
        trace = ''.join(traceback.format_exception(*self._exception)).strip()
        value.formatted_traceback = trace

        # Wake any threads waiting on us.  We've initialized _exception with
        # the traceback object, so any threads that access the result property
        # between now and the end of this function will have an opportunity to
        # get the live traceback.
        self._finished_event_poke(set=True)

        if self._exception_signal.count() == 0:
            # There are no exception handlers, so we know we will end up
            # queuing the traceback in the exception signal.  Set it to None
            # to prevent that.
            tb = None

        if self._exception_signal.emit_when_handled(type, value, tb) == False:
            # A handler has acknowledged handling this exception by returning
            # False.  So we won't log it.
            self._unhandled_exception = None

        # If we were thrown an InProgressAborted, the likely reason is an
        # InProgress we were waiting on has been aborted.  In this case, we
        # emit the abort signal and clear _unhandled_exception, provided there
        # are callbacks connected to the abort signal.  Otherwise, do not
        # clear _unhandled_exception so that it gets logged.
        if isinstance(value, InProgressAborted) and len(self.signals['abort']):
            if not aborted:
                self.signals['abort'].emit(value)
            self._unhandled_exception = None

        if self._unhandled_exception:
            # This exception was not handled synchronously, so we set up a
            # weakref object with a finalize callback to a function that
            # logs the exception.  We could do this in __del__, except that
            # the gc refuses to collect objects with a destructor.  The weakref
            # kludge lets us accomplish the same thing without actually using
            # __del__.
            #
            # If the exception is passed back via result property, then it is
            # considered handled, and it will not be logged.
            cb = Callable(InProgress._log_exception, trace, value, self._stack)
            self._unhandled_exception = _weakref.ref(self, cb)
            _unhandled_exceptions.add(self._unhandled_exception)

        # Remove traceback from stored exception.  If any waiting threads
        # haven't gotten it by now, it's too late.
        if not isinstance(value, AsyncExceptionBase):
            value = AsyncException(value, stack)
        if hasattr(value, 'with_traceback'):
            # Remove traceback attached to exception objects in Python 3.
            value = value.with_traceback(None)
        self._exception = value.__class__, value, None

        # cleanup
        self.disconnect_all()
        self._exception_signal.disconnect_all()
        self.signals['abort'].disconnect_all()

        # We return False here so that if we've received a thrown exception
        # from another InProgress we're waiting on, we essentially inherit
        # the exception from it and indicate to it that we'll handle it
        # from here on.  (Otherwise the linked InProgress would figure
        # nobody handled it and would dump out an unhandled async exception.)
        return False

    @classmethod
    def _log_exception(cls, weakref, trace, exc, create_stack):
        """
        Callback to log unhandled exceptions.
        """
        _unhandled_exceptions.remove(weakref)
        if isinstance(exc, (KeyboardInterrupt, SystemExit)):
            # We have an unhandled asynchronous SystemExit or KeyboardInterrupt
            # exception.  Rather than logging it, we reraise it in the main
            # loop so that the main loop exception handler can act
            # appropriately.
            def reraise():
                raise exc
            from .main import signals
            return signals['step'].connect_once(reraise)

        try:
            log.error('Unhandled %s exception:\n%s', cls.__name__, trace)
        except Exception:
            # The logger raised an exception, which probably means something
            # fairly serious and unrecoverable has happened (such as too many
            # open files).  Out of desperation, now just print to stderr.
            sys.stderr.write('\nFATAL: logger failed during an unhandled %s exception:\n%s\n' % \
                             (cls.__name__, trace))
            return

        if log.getEffectiveLevel() <= logging.DEBUG:
            # Asynchronous exceptions create a bit of a problem in that while you
            # know where the exception came from, you don't easily know where it
            # was going.  Here we dump the stack obtained in the constructor,
            # so it's possible to find out which caller didn't properly catch
            # the exception.
            create_tb = ''.join(traceback.format_list(create_stack))
            log.info('Create-stack for InProgress from preceding exception:\n%s', create_tb)


    def abort(self, exc=None):
        """
        Aborts the asynchronous task this InProgress represents.

        :param exc: optional exception object with which to abort the InProgress; if
                    None is given, a general :class:`~kaa.InProgressAborted`
                    exception will be used.
        :type exc: :class:`~kaa.InProgressAborted` or subclass thereof

        Not all such tasks can be aborted.  If aborting is not supported, or if
        the InProgress is already finished, a RuntimeError exception is raised.
        """
        if self.finished:
            raise RuntimeError('InProgress is already finished.')

        if exc is None:
            exc = InProgressAborted('InProgress task aborted by abort()', inprogress=self)
        elif not isinstance(exc, InProgressAborted):
            raise ValueError('Exception must be instance of InProgressAborted (or subclass thereof)')

        if not self.abortable or self.signals['abort'].emit(exc) == False:
            raise RuntimeError('%s cannot be aborted.' % self)

        if exc.inprogress != self:
            # We're being aborted with an InProgressAborted created by a different
            # InProgress (one we're linked to?), so create a new exception object,
            # preserving the origin but replacing the inprogress attribute.
            exc = exc.__class__(*exc.args, inprogress=self, origin=exc.origin)
        elif not exc.origin:
            # InProgressAborted lacks origin, so start with self.
            exc.origin = self
        self.throw(exc.__class__, exc, None, aborted=True)


    def timeout(self, timeout, callback=None, abort=False):
        """
        Create a new InProgress object linked to this one that will throw
        :class:`~kaa.TimeoutException` if this object is not finished by the
        given timeout.

        :param callback: called (with no additional arguments) just prior
                         to TimeoutException
        :type callback: callable
        :param abort: invoke :meth:`~kaa.InProgress.abort` on the original InProgress
                      if the timeout occurs.
        :type abort: bool
        :return: a new :class:`~kaa.InProgress` object that is subject to the timeout

        If the original InProgress finishes before the timeout, the new InProgress
        (returned by this method) is finished with the result of the original.  If
        :meth:`abort` is called on the returned InProgress, the original one will
        also be aborted.

        If a timeout does occur and the ``abort`` argument is False, the
        original InProgress object is not affected: it is not finished with the
        :class:`~TimeoutException`, nor is it aborted.  You can explicitly
        abort the original InProgress::

            @kaa.coroutine()
            def read_from_socket(sock):
                try:
                    data = yield sock.read().timeout(3)
                except kaa.TimeoutException as e:
                    print 'Error:', e.args[0]
                    e.inprogress.abort()

        If you set ``abort=True`` then the original InProgress is aborted
        automatically, but *before* the TimeoutException is thrown into the new
        InProgress returned by this method.  This allows a coroutine being
        aborted to perform cleanup actions before relinquishing control back to
        the caller.  In this example, sock.read() will be aborted if not
        completed within 3 seconds::

            @kaa.coroutine()
            def read_from_socket(sock):
                data = yield sock.read().timeout(3, abort=True)
        """
        async = InProgress()
        def trigger():
            self.disconnect(async.finish)
            self._exception_signal.disconnect(async.throw)
            if not async._finished:
                if callback:
                    callback()
                msg = 'InProgress timed out after %.02f seconds' % timeout
                exc = TimeoutException(msg, inprogress=self)
                try:
                    if abort:
                        # In the case of a coroutine, abort() will raise the supplied exc if there
                        # are no abort handlers.  But we've already thrown a timeout into async,
                        # and this closure is invoked from the notifier (via a timer) and can't
                        # do anything about the exception anyway.  So suppress InProgressAborted
                        # exceptions raised by abort().
                        try:
                            self.abort(exc)
                        except InProgressAborted:
                            pass
                finally:
                    async.throw(exc.__class__, exc, None)


        async.waitfor(self)
        from .timer import OneShotTimer
        timer = OneShotTimer(trigger)
        timer.start(timeout)

        # Add an abort handler to the new InProgress.  If it's aborted,
        # cleanup, and if abort=True then abort self.
        def handle_abort(exc):
            self.disconnect(async.finish)
            self._exception_signal.disconnect(async.throw)
            timer.stop()
            if abort and not self.finished:
                self.abort(exc)

        async.signals['abort'].connect(handle_abort)
        return async


    def noabort(self):
        """
        Create a new InProgress object for this task that cannot be aborted.

        :return: a new :class:`~kaa.InProgress` object that finishes when self
                 finishes, but will raise if an :meth:`abort` is attempted
        """
        ip = InProgress(abortable=False)
        ip.waitfor(self)
        return ip


    def execute(self, func, *args, **kwargs):
        """
        Execute the given function and finish the InProgress object with the
        result or exception.

        If the function raises SystemExit or KeyboardInterrupt, those are
        re-raised to allow them to be properly handled by the main loop.

        :param func: the function to be invoked
        :type func: callable
        :param args: the arguments to be passed to the function
        :param kwargs: the keyword arguments to be passed to the function
        :return: the InProgress object being acted upon (self)
        """
        try:
            result = func(*args, **kwargs)
        except BaseException, e:
            self.throw()
            if isinstance(e, (KeyboardInterrupt, SystemExit)):
                # Reraise these exceptions to be handled by the mainloop
                raise
        else:
            self.finish(result)
        return self


    def wait(self, timeout=None):
        """
        Blocks until the InProgress is finished.

        The main loop is kept alive if waiting in the main thread, otherwise
        the thread is blocked until another thread finishes the InProgress.

        If the InProgress finishes due to an exception, that exception is
        raised.

        :param timeout: if not None, wait() blocks for at most timeout seconds
                        (which may be fractional).  If wait times out, a
                        TimeoutException is raised.
        :return: the value the InProgress finished with
        """
        # Connect a dummy handler to ourselves.  This is a bit kludgy, but
        # solves a particular problem with InProgress(Any|All), which don't
        # actually finish unless something wants to know.  Normally, without
        # wait, we are yielded to the coroutine wrapper which implicitly
        # connects to us.  Here, with wait(), in a sense we want to know when
        # self finishes.
        dummy = lambda *args, **kwargs: None
        self.connect(dummy)

        from . import main
        if CoreThreading.is_mainthread():
            # We're waiting in the main thread, so we must keep the mainloop
            # alive by calling main.loop() until we're finished.
            main.loop(lambda: not self.finished, timeout)
        elif not main.is_running():
            # Seems that no loop is running, try to loop
            try:
                main.loop(lambda: not self.finished, timeout)
            except RuntimeError:
                # Main loop started in another thread between the time we checked and
                # tried to start the loop.  Now just wait on the thread event.
                self._finished_event_poke(wait=timeout)
        else:
            # We're waiting in some other thread, so wait for some other
            # thread to wake us up.
            self._finished_event_poke(wait=timeout)

        if not self.finished:
            self.disconnect(dummy)
            raise TimeoutException('Timed out', inprogress=self)

        return self.result


    def waitfor(self, inprogress):
        """
        Connects to another InProgress object (A) to self (B).  When A finishes
        (or throws), B is finished with the result or exception.

        :param inprogress: the other InProgress object to link to.
        :type inprogress: :class:`~kaa.InProgress`
        """
        inprogress.connect_both(self.finish, self.throw)


    def _connect(self, callback, args = (), kwargs = {}, once = False,
                 weak = False, pos = -1):
        """
        Internal connect function. Always set once to True because InProgress
        will be emited only once.
        """
        return Signal._connect(self, callback, args, kwargs, True, weak, pos)


    def connect_both(self, finished, exception=None):
        """
        Convenience function that connects a callback (or callbacks) to both
        the InProgress (for successful result) and exception signals.

        This function does not accept additional args/kwargs to be passed to
        the callbacks.  If you need that, use :meth:`~kaa.InProgress.connect`
        and :attr:`~kaa.InProgress.exception`.connect().

        If *exception* is not given, the given callable will be used for **both**
        success and exception results, and therefore must be able to handle variable
        arguments (as described for each callback below).

        :param finished: callback to be invoked upon successful completion; the
                         callback is passed a single argument, the result returned
                         by the asynchronous task.
        :param exception: (optional) callback to be invoked when the asynchronous task
                          raises an exception; the callback is passed three arguments
                          representing the exception: exception class, exception
                          instance, and traceback.
        """
        if exception is None:
            exception = finished
        self.connect(finished)
        self._exception_signal.connect_once(exception)



class InProgressCallable(InProgress):
    """
    A callable variant of InProgress that finishes when invoked.
    """
    def __init__(self, func=None, abortable=None, frame=0, throwable=True):
        """
        :param func: if defined, is invoked on initialization and self is
                     passed as the only argument.  Intended as a convenience.
        :type func: callable
        :param frame: corresponds to the abortable property in
            :class:`~kaa.InProgress`
        :param throwable: if True, if the InProgressCallable is invoked with 3
            arguments (tp, exc, value) then :meth:`~kaa.InProgress.throw` is called
            instead of :meth:`~kaa.InProgress.finish`.

        The main value of the InProgressCallable is the translation done
        between the arguments passed on invocation and those passed to
        :meth:`~kaa.InProgress.finish`.  A single positional or named
        argument is passed as the value to ``finish()``; multiple positional
        *or* multiple named arguments are passed as a tuple or dict respectively;
        otherwise the InProgress is finished with a 2-tuple of (args, kwargs).

        If ``throwable`` is True (default) and the callable is invoked with
        the standard exception 3-tuple (type, value, traceback), then it's
        treated as an exception which is thrown to the InProgress.

        The primary use-case for the InProgressCallable is to marry
        conventional callbacks for asynchronous task completion with the
        InProgress strategy.
        """
        super(InProgressCallable, self).__init__(abortable, frame=frame-1)
        self._throwable = throwable
        if func is not None:
            # connect self as callback
            func(self)


    def __call__(self, *args, **kwargs):
        """
        Call the InProgressCallable by the external function. This will
        finish the InProgress object.
        """
        # try to get the results as the caller excepts them
        if self._throwable and len(args) == 3 and issubclass(args[0], BaseException):
            return self.throw(*args)
        if args and kwargs:
            # no idea how to merge them
            return self.finish((args, kwargs))
        if kwargs and len(kwargs) == 1:
            # return the value
            return self.finish(kwargs.values()[0])
        if kwargs:
            # return as dict
            return self.finish(kwargs)
        if len(args) == 1:
            # return value
            return self.finish(args[0])
        if len(args) > 1:
            # return as list
            return self.finish(args)
        return self.finish(None)


class InProgressAny(InProgress):
    """
    InProgress object that finishes when *any* of the supplied InProgress
    objects (in constructor) finish.

    Sequences or generators passed as arguments will be flattened, allowing
    for this idiom::

        yield InProgressAny(func() for func in coroutines)

    Arguments will be passed through :func:`kaa.inprogress` so any object that
    can be coerced to an :class:`~kaa.InProgress` (such as
    :class:`~kaa.Signal` objects) can be passed directly.

    .. note::
       Callbacks aren't attached to the supplied InProgress objects to monitor
       their state until a callback is attached to the InProgressAny object.
       This means an InProgressAny with nothing connected will not actually
       finish even when one of its constituent InProgresses finishes.

    :param finish: controls what values the InProgressAny is finished with
    :type finish: ``FINISH_IDX_RESULT`` (default), ``FINISH_IDX``, or
        ``FINISH_RESULT``
    :param filter: optional callback receiving two arguments (index and
        finished result) invoked each time an underlying InProgress object
        finishes which, if returns True, prevents the completion of the
        InProgressAny iff there are other InProgress objects that could
        yet finish.
    :type filter: callable

    The possible ``finish`` values are:

        * ``kaa.FINISH_IDX_RESULT``: a 2-tuple (idx, result) containing
          the index (relative to the position of the InProgress passed to
          the constructor) and the result that InProgress finished with
        * ``kaa.FINISH_IDX``: the index (offset from 0) of the InProgress
          that finished the InProgressAny
        * ``kaa.FINISH_RESULT``: the result of the InProgress that
          finished the InProgressAny

    For example::

        # Read data from either sock1 or sock2, whichever happens first within
        # 2 seconds.
        idx, data = yield kaa.InProgressAny(kaa.delay(2), sock1.read(), sock2.read())
        if idx == 0:
            print 'Nothing read from either socket after 2 seconds'
        else:
            print 'Read from sock{0}: {1}'.format(idx, data)


    """
    _default_finish_args = FINISH_IDX_RESULT

    def __init__(self, *objects, **kwargs):
        self._finish_args = kwargs.pop('finish', None) or self._default_finish_args
        self._filter = kwargs.pop('filter', None)

        if 'pass_index' in kwargs:
            # Legacy behaviour.
            log.warning('pass_index argument to InProgressAny() is deprecated; use finish')
            self._finish_args = FINISH_IDX_RESULT if kwargs.pop('pass_index') else FINISH_RESULT

        if self._finish_args not in (FINISH_RESULT, FINISH_SELF, FINISH_IDX_RESULT, FINISH_IDX):
            raise ValueError('invalid finish kwarg')

        super(InProgressAny, self).__init__(**kwargs)
        # Generate InProgress objects for anything that was passed, including
        # InProgress objects nested within sequences and generators.
        self._objects = [inprogress(o) for o in self._flatten(objects)]
        self._counter = len(self._objects) or 1

        self._prefinished_visited = set()
        self._check_prefinished()


    def _flatten(self, v):
        if isinstance(v, dict) and not hasattr(v, '__inprogress__'):
            # This works for Signals objects.
            v = v.values()
        if isinstance(v, (list, tuple, types.GeneratorType)):
            for item in iter(v):
                for sub in self._flatten(item):
                    yield sub
        else:
            yield v


    def _get_connect_args(self, ip, n):
        """
        Called for each InProgress we connect to, and returns arguments to be
        passed to self.finish if that InProgress finishes.
        """
        return (n,)


    def _check_prefinished(self):
        """
        Determine if any of the given IP objects were passed to us already finished,
        which may in turn finish us immediately.
        """
        prefinished = []
        for n, ip in enumerate(self._objects):
            if ip.finished and id(ip) not in self._prefinished_visited:
                prefinished.append(n)
                self._prefinished_visited.add(id(ip))
        self._finalize_prefinished(prefinished)


    def _finalize_prefinished(self, prefinished):
        """
        Called from _check_prefinished.  prefinished is a list of indexes
        (relative to self._objects) that were already finished when we tried to
        connect to them.

        This logic is done in a separate method (instead of in _check_prefinished)
        so that subclasses can override this behaviour (without duplicating the
        common code in _check_prefinished).
        """
        if not prefinished:
            return

        # One or more IP was already finished.  We pass each one to
        # self.finish until we're actually finished (because the prefinished
        # IP may get filtered).
        while not self.finished and prefinished:
            idx = prefinished.pop(0)
            ip = self._objects[idx]
            if ip.failed:
                self.finish(True, idx, ip._exception)
            else:
                self.finish(False, idx, ip.result)


    def _changed(self, action):
        """
        Called when a callback connects or disconnects from us.
        """
        if not self._objects:
            # Already finished.  This can happen when IPAny finishes, and
            # then wait() is called on it.  One possible normal scenario for
            # this is when wait() is called in another thread.  If the IP is
            # finished by the mainthread before wait() is called, then we
            # don't want to attempt to iterate over _objects, which was set
            # to None in finish().
            return super(InProgressAny, self)._changed(action)

        if len(self) == 1 and action == Signal.CONNECTED and not self.finished:
            # Someone wants to know when we finish, so now we connect to the
            # underlying InProgress objects to find out when they finish.
            self._check_prefinished()
            # _check_prefinished() could have implicitly called finish(),
            # setting self._objects to None.
            if self._objects:
                for n, ip in enumerate(self._objects):
                    if ip.finished:
                        # This one is finished already, no need to connect to it.
                        continue
                    args = self._get_connect_args(ip, n)
                    ip.connect(self.finish, False, *args).init_args_first = True
                    ip.exception.connect(self.finish, True, *args).init_args_first = True

        elif len(self) == 0 and action == Signal.DISCONNECTED:
            for ip in self._objects:
                ip.disconnect(self.finish)
                ip.exception.disconnect(self.finish)

        return super(InProgressAny, self)._changed(action)


    def finish(self, is_exception, index, *result):
        """
        Invoked when any one of the InProgress objects passed to the
        constructor have finished.
        """
        # FIXME: rethink how we handle prerequisites that finish
        # by exception.  Should we throw too?
        result = result[0] if not is_exception else result
        self._counter -= 1
        if self._filter and self._filter(result) and self._counter > 0:
            # Result is filtered and there are other InProgress candidates,
            # so we'll wait for them.
            return

        if self._finish_args == FINISH_IDX_RESULT:
            finish_result = index, result
        elif self._finish_args == FINISH_RESULT:
            finish_result = result
        elif self._finish_args == FINISH_IDX:
            finish_result = index
        elif self._finish_args == FINISH_SELF:
            # Not really useful because _objects is about to be cleared out,
            # but included for completeness.
            finish_result = self

        # We're done with the underlying IP objects so unref them.  In the
        # case of InProgressCallable connected weakly to signals (which
        # happens when signals are given to us on the constructor), they'll
        # get deleted and disconnected from the signals.
        #
        # Small nicety: if we clear out _objects before calling
        # InProgress.finish() then we force the disconnection of
        # inprogress()ed Signal objects before (potentially) resuming any
        # coroutine that yielded this InProgressAny.
        self._objects = None

        super(InProgressAny, self).finish(finish_result)



class InProgressAll(InProgressAny):
    """
    InProgress object that finishes only when *all* of the supplied InProgress
    objects (in constructor) finish.

    The InProgressAll object then finishes with itself. The finished
    InProgressAll is useful to fetch the results of the individual InProgress
    objects.  It can be treated as an iterator, and can be indexed::

        for ip in (yield kaa.InProgressAll(sock1.read(), sock2.read())):
            print(ip.result)
    """
    _default_finish_args = FINISH_SELF

    def _get_connect_args(self, ip, n):
        return ()


    def _finalize_prefinished(self, prefinished):
        if len(prefinished) == len(self._objects):
            # All underlying InProgress objects are already finished so we're
            # done.  Prime counter to 1 to force finish() to actually finish
            # when we call it next.
            self._counter = 1
            self.finish(False, None)
        elif len(prefinished):
            # Some underlying InProgress objects are already finished so we
            # need to subtract them from the number of objects we are still
            # waiting for.
            self._counter -= len(prefinished)


    def finish(self, is_exception, *result):
        # FIXME: rethink how we handle prerequisites that finish
        # by exception.  Should we throw too?
        self._counter -= 1
        if self._counter > 0:
            # Still more prerequisites to finish before we can finish.
            return

        if self._finish_args == FINISH_SELF:
            finish_result = self
        else:
            all_results = [(idx, ip.result if not ip.failed else ip._exception)
                                           for idx, ip in enumerate(self._objects)]
            if self._finish_args == FINISH_IDX_RESULT:
                finish_result = all_results
            elif self._finish_args == FINISH_RESULT:
                finish_result = [result for idx, result in all_results]
            elif self._finish_args == FINISH_IDX:
                # Hardly useful, but added for completeness.
                finish_result = [idx for idx, result in all_results]

        # Note that this calls InProgress.finish(), not InProgressAny.finish().
        super(InProgressAny, self).finish(finish_result)
        # Unlike InProgressAny, we don't unref _objects because the caller
        # may want to access them by iterating us.  That's fine, because
        # unlike InProgressAny where we'd prefer not to have useless
        # transient InProgressCallables connected to any provided signals,
        # here we know we won't because they will all have been emitted
        # in order for us to be here.


    def __iter__(self):
        return iter(self._objects)


    def __getitem__(self, idx):
        return self._objects[idx]
