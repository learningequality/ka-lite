# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - provides core functionality needed by most kaa.base modules
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2010-2012 Dirk Meyer, Jason Tackaberry, et al.
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
from __future__ import absolute_import, with_statement

__all__ = ['Object', 'Signal', 'Signals', 'CoreThreading']

# python imports
import inspect
import logging
import atexit
import threading
import sys
import os
import fcntl
import signal
import time
import errno
import Queue

# kaa imports
from .callable import Callable, WeakCallable, CallableError
from .utils import property
from .strutils import bl
from . import nf_wrapper as notifier

# get logging object
log = logging.getLogger('kaa.base.core')


class CoreThreading:
    """
    CoreThreading is a namespace (not intended to be instantiated) holding
    various common threading and mainloop functionality that is required by
    many different modules in Kaa.
    """
    # Variable that is set to True (via atexit callback) when python
    # interpreter is in the process of shutting down.  If we're interested if
    # the interpreter is shutting down, we don't want to test that this
    # variable is True, but rather that it is not False, because as it is
    # prefixed with an underscore, the interpreter might already have deleted
    # this variable in which case it is None.
    python_shutting_down = False

    # The amount of time (in seconds) the main thread can be blocked while
    # executing callbacks that were queued to be invoked from the main loop.
    mainthread_callback_max_time = 2.0

    # Internal only attributes.
    #
    # The thread pipe, which is created by CoreThreading.init(), is used
    # to awaken the main loop.  This happens in CoreThreading.queue_callback()
    # and CoreThreading.wakeup().  XXX: this pipe must not be carried through
    # to forked children, or ugly behaviour will ensue.  kaa.utils.fork() and
    # .daemonize() will ensure a new pipe is created in the child process.
    _pipe = None
    # The signal wake pipe.  We pass the write side of the pipe to Python's
    # signal.set_wakeup_fd(), and any time there is a unix signal received
    # for which there has been a Python handler attached, the interpreter
    # will write a byte to the pipe.  We monitor the read end in the
    # notifier, which causes the main thread to wake up if we receive a
    # unix signal.  This is necessary because signals are not guaranteed to be
    # received by the main thread, but Python always queues the handler to be
    # executed from the main thread.  Without this, we could wait up to 30
    # seconds (the maximum sleep time in notifier) to handle a signal.
    _signal_wake_pipe = None
    # Holds a queue of callbacks and their arguments that need to be executed
    # from the main loop (by CoreThreading.run_queue, which is called by the
    # notifier when there is activity on the pipe.)  The queue has some fairly
    # large upper limit to prevent suicide-by-queuing.  See run_queue() for
    # more details.
    _queue = Queue.Queue(10000)
    # Mutex to ensure put/qsize is atomic in queue_callback()
    _queue_put_lock = threading.Lock()
    _mainthread = threading.currentThread()
    # Create a one byte dummy token for writing to the pipe.  Normally we'd
    # just use b'1' but Python 2.5 can't parse it.
    _PIPE_NOTIFY_TOKEN = bl('1')


    @staticmethod
    def init(signals, purge=False):
        """
        Initialize the core threading/mainloop functionality by creating the
        thread notifier and signal wakeup pipes, and registering them with
        the notifier.

        :param signals: the main loop Signals object (passed by main.py)
        :param purge: if True, any pending callbacks queued for execution in
                      the mainloop will be removed.  This is useful when we have
                      forked and want to wipe the slate clean.

        This function also installs a SIGCHLD handler, mainly for lack of a
        better place.

        If this function is called multiple times, it must recreate the pipes
        and cleanup after previous invocations.
        """
        log.debug('Creating thread notifier and signal wakeup pipes (purge=%s)', purge)
        if CoreThreading._pipe:
            # There is an existing pipe already, so stop monitoring it.
            notifier.socket_remove(CoreThreading._pipe[0])
        CoreThreading._pipe = CoreThreading._create_nonblocking_pipe()
        notifier.socket_add(CoreThreading._pipe[0], CoreThreading.run_queue)

        if purge:
            while not CoreThreading._queue.empty():
                CoreThreading._queue.get()
        elif not CoreThreading._queue.empty():
            # A thread is already running and wanted to run something in the
            # mainloop before the mainloop is started. In that case we need
            # to wakeup the loop ASAP to handle the requests.
            CoreThreading._wakeup()


        # Create wakeup fd pipe (Python 2.6) and install SIGCHLD handler.
        if hasattr(signal, 'set_wakeup_fd'):
            # Python 2.6+, so setup the signal wake pipe.
            if CoreThreading._signal_wake_pipe:
                # Stop monitoring old signal wake pipe.
                notifier.socket_remove(CoreThreading._signal_wake_pipe[0])
            pipe = CoreThreading._create_nonblocking_pipe()
            CoreThreading._signal_wake_pipe = pipe
            # _purge_pipe() returns None, which will not unregister the socket
            # handler.
            notifier.socket_add(pipe[0], CoreThreading._purge_pipe)
            signal.set_wakeup_fd(pipe[1])

        signal.signal(signal.SIGCHLD, Callable(CoreThreading._handle_generic_unix_signal, signals))
        # Emit 'sigchld' now to reap processes that may have terminated
        # before we set the handler.  process.py connects to this signal.
        signals['sigchld'].emit()


    @staticmethod
    def _handle_generic_unix_signal(signum, frame, signals):
        log.debug('received signal %d (%s)', signum,
                  '%s:%d' % (frame.f_code.co_filename, frame.f_lineno) if frame else 'no frame')
        timer_id = None
        # Create a new closure to be registered with the notifier for
        # invocation to emit the appropriate signal.  We can't use the
        # OneShotTimer goodness from kaa.timer since CoreThreading is lower
        # level than that.
        def notifier_handler_cb():
            # Explicitly unregister the timer now in case something raises
            # below and we don't get a chance to return False.
            notifier.timer_remove(timer_id)
            if signum == signal.SIGCHLD:
                signals['sigchld'].emit()
        timer_id = notifier.timer_add(0, notifier_handler_cb)


    @staticmethod
    def _create_nonblocking_pipe():
        pipe = os.pipe()
        for fd in pipe:
            flags = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, flags | os.O_NONBLOCK)
            flags = fcntl.fcntl(fd, fcntl.F_GETFD)
            fcntl.fcntl(fd, fcntl.F_SETFD, flags | fcntl.FD_CLOEXEC)
        return pipe


    @staticmethod
    def _purge_pipe(fd):
        """
        Purges all data from the given file descriptor.  Silently ignores
        EAGAIN under the assumption that the pipe is used for some sort of
        wakeup and the wakeup has happened, so it's not worth complaining
        about.  In any case, the select(2) man page says that on Linux, there
        may be "circumstances in which a file descriptor is spuriously reported
        as ready."

        Other errors are raised to the caller.
        """
        try:
            while os.read(fd, 4096) == 4096:
                pass
        except (IOError, OSError), (err, msg):
            if err != errno.EAGAIN:
                raise


    @staticmethod
    def queue_callback(callback, args, kwargs, in_progress):
        # We need to synchronize the put and qsize calls or we might not
        # realize we need to wakeup. (e.g. two threads can do put() one after
        # the other, and then the call to qsize() would be 2.)  We don't care
        # if the get() in run_queue() means we miss wakeup() because if
        # run_queue() is running then clearly we're already woken up. :)
        with CoreThreading._queue_put_lock:
            CoreThreading._queue.put((callback, args, kwargs, in_progress))
            if CoreThreading._queue.qsize() == 1:
                # We just added the first callback to the queue, so notify the
                # mainthread.
                CoreThreading._wakeup()


    @staticmethod
    def run_queue(fd):
        try:
            CoreThreading._purge_pipe(CoreThreading._pipe[0])
        except (IOError, OSError), (err, msg):
            # Some error occurred while reading from the wakeup pipe.  We don't
            # let the exception bubble up to the main loop however, because
            # whatever the problem may be, we are at least now awake as
            # intended, and need to execute any queued callbacks.  Log a
            # warning instead.
            log.warning('Problem reading from thread notifier pipe: [%d] %s', err, msg)


        # It's possible that a thread is actively enqueuing callbacks faster
        # than we can dequeue and invoke them.  207fc3af77 tried to fix this by
        # locking the queue for the entire loop, but this introduced a
        # deadlock caused when a thread enqueues a callback while a previously
        # queued callback is being invoked and is blocked on a resource used
        # by that thread (like a different mutex).
        #
        # So we don't lock the whole loop to avoid the deadlock, and we stop
        # invoking callbacks after mainthread_callback_max_time seconds
        # has elapsed in order to solve the problem 207fc3af77 tried to fix.
        #
        # Now, there is a large upper bound on the queue to prevent memory
        # exhaustion, which means a producer will block if it's adding
        # callbacks too quickly, which means we could still deadlock if both
        # the above scenarios is true (i.e. a thread is enqueuing callbacks
        # faster than the main loop can process them, _and_ a mainthread
        # callback is blocking on a resource held by that thread).  But
        # hopefully we have pushed that to an extreme corner case -- although
        # probably at the expense of making that corner case harder to
        # find/debug. :(
        t0 = time.time()
        while not CoreThreading._queue.empty():
            if time.time() - t0 > CoreThreading.mainthread_callback_max_time:
                # We've spent too much time blocking the main loop invoking the
                # queued callbacks, but we still have more.  Poke the thread
                # pipe so the next iteration of the main loop calls us back
                # and abort the loop.
                CoreThreading._wakeup()
                break

            callback, args, kwargs, in_progress = CoreThreading._queue.get()
            try:
                in_progress.finish(callback(*args, **kwargs))
            except BaseException, e:
                # All exceptions, including SystemExit and KeyboardInterrupt,
                # are caught and thrown to the InProgress, because it may be
                # waiting in another thread.  However SE and KI are reraised
                # in here the main thread so they can be propagated back up
                # the mainloop.
                in_progress.throw()
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
        return True

    @staticmethod
    def _wakeup():
        """
        Wakes up the mainloop.  This is the private interface, which always
        writes a byte to the notifier pipe.
        """
        if CoreThreading._pipe:
            os.write(CoreThreading._pipe[1], CoreThreading._PIPE_NOTIFY_TOKEN)


    @staticmethod
    def wakeup():
        """
        Wakes up the mainloop.

        The mainloop sleeps when there are no timers to process and no activity on
        any registered :class:`~kaa.IOMonitor` objects.  This function can be used
        by another thread to wake up the mainloop.  For example, when a
        :class:`~kaa.MainThreadCallable` is invoked, it calls ``wakeup()``.
        """
        # Only need to write to the pipe if the queue is empty; if it's not
        # empty, then queue_callback() would have called _wakeup().
        if CoreThreading._queue.empty():
            os.write(CoreThreading._pipe[1], CoreThreading._PIPE_NOTIFY_TOKEN)


    @staticmethod
    def is_mainthread():
        """
        Return True if the current thread is the main thread.

        Note that the "main thread" is considered to be the thread in which the
        kaa main loop is running.  This is usually, but not necessarily, what
        Python considers to be the main thread.  (If you call :func:`kaa.main.run`
        in the main Python thread, then they are equivalent.)
        """
        # If threading module is None, assume main thread.  (Silences pointless
        # exceptions on shutdown.)
        return (not threading) or threading.currentThread() == CoreThreading._mainthread


    @staticmethod
    def set_as_mainthread():
        """
        Set the current thread as mainthread. This function SHOULD NOT be called
        from the outside, the loop function is setting the mainthread if needed.
        """
        CoreThreading._mainthread = threading.currentThread()


    def _handle_shutdown():
        CoreThreading.python_shutting_down = True
    atexit.register(_handle_shutdown)



class Object(object):
    """
    Base class for kaa objects.

    This class contains logic to convert the __kaasignals__ class attribute
    (a dict) into a signals instance attribute (a kaa.Signals object).

    __kaasignals__ is a dict whose key is the name of the signal, and value
    a docstring.  The dict and docstring should be formatted like so::

        ___kaasignals__ = {
            'example':
                '''
                Single short line describing the signal.

                .. describe:: def callback(arg1, arg2, ...)

                   :param arg1: Description of arg1
                   :type arg1: str
                   :param arg2: Description of arg2
                   :type arg2: bool

                A more detailed description of the signal, if necessary, follows.
                ''',

            'another':
                '''
                Docstring similar to the above example.  Note the blank line
                separating signal stanzas.
                '''
        }

    It is possible for a subclass to remove a signal provided by its superclass
    by setting the dict value to None.  e.g.::

        __kaasignals__ = {
            'newsignal':
                '''
                New signal provided by this subclass.
                ''',

            # This ensures the signal 'supersignal' does not appear in the
            # current class's kaa.Signals object.  (It does not affect the
            # superclass.)
            'supersignal': None
        }
    """
    @staticmethod
    def _get_all_signals(cls):
        """
        Merge __kaasignals__ dict for the entire inheritance tree for the given
        class.  Newer (most descended) __kaasignals__ will replace older ones if
        there are conflicts.
        """
        cached_attr = '__kaasignals_%s_cached__' % cls.__name__
        signals = getattr(cls, cached_attr, None)
        if signals is None:
            signals = {}
            for c in reversed(inspect.getmro(cls)):
                if hasattr(c, '__kaasignals__'):
                    signals.update(c.__kaasignals__)

            # Remove all signals whose value is None.
            [ signals.pop(k) for k, v in signals.items() if v is None ]
            setattr(cls, cached_attr, signals)
        return signals


    def __init__(self, *args, **kwargs):
        # Accept all args, and pass to superclass.  Necessary for kaa.Object
        # descendants to be involved in inheritance diamonds.
        super(Object, self).__init__(*args, **kwargs)

        signals = self._get_all_signals(self.__class__)
        if signals:
            # Construct the kaa.Signals object and attach the docstrings to
            # each signal in the Signal object's __doc__ attribute.
            self.signals = Signals(*signals.keys())
            if 'sphinx.builders' in sys.modules:
                # Tiny optimization: only add docstring if we're doing doc
                # generation.
                for name in signals:
                    self.signals[name].__doc__ = signals[name]


class Signal(object):
    """
    Create a Signal object to which callbacks can be connected and later
    invoked in sequence when the Signal is emitted.
    """
    # Defines the maximum number of connections to a signal.  Attempting to
    # connect more than this many callbacks will trigger an exception.
    MAX_CONNECTIONS = 1000
    # Constants used for the action parameter for changed_cb.
    CONNECTED = 1
    DISCONNECTED = 2

    def __init__(self, changed_cb=None):
        """
        :param changed_cb: corresponds to the :attr:`~kaa.Signal.changed_cb` property.
        :type changed_cb: callable
        """
        super(Signal, self).__init__()
        self._callbacks = []
        self.changed_cb = changed_cb
        self._deferred_args = []


    @property
    def changed_cb(self):
        """
        Callable to be invoked whenever a callback is connected to or
        disconnected from the Signal.

        .. describe:: def callback(signal, action)

           :param signal: the :class:`~kaa.Signal` object acted upon
           :param action: either ``kaa.Signal.CONNECTED`` or ``kaa.Signal.DISCONNECTED``
        """
        return self._changed_cb


    @changed_cb.setter
    def changed_cb(self, callback):
        assert(callback is None or callable(callback))
        self._changed_cb = callback


    @property
    def callbacks(self):
        """
        Tuple containing the callbacks connected to this signal.

        Because this value is a tuple, it cannot be manipulated directly.  Use
        :meth:`~kaa.Signal.connect` and :meth:`~kaa.Signal.disconnect` instead.
        """
        return tuple(self._callbacks)


    def __iter__(self):
        for cb in self._callbacks:
            yield cb


    def __len__(self):
        return len(self._callbacks)


    def __nonzero__(self):
        return True


    def __contains__(self, key):
        if not callable(key):
            return False

        for cb in self._callbacks:
            if cb == key:
                return True

        return False

    def _connect(self, callback, args = (), kwargs = {}, once = False, weak = False, pos = -1):
        """
        Connects a new callback to the signal.  args and kwargs will be bound
        to the callback and merged with the args and kwargs passed during
        emit().  If weak is True, a WeakCallable will be created.  If once is
        True, the callback will be automatically disconnected after the next
        emit().

        This method returns the Callable (or WeakCallable) object created.
        """
        if not callable(callback):
            raise TypeError('callback must be callable, got %s instead.' % callback)

        if len(self._callbacks) >= Signal.MAX_CONNECTIONS:
            raise ValueError('Number of callbacks exceeds Signal.MAX_CONNECTIONS limit (%d)' % Signal.MAX_CONNECTIONS)

        if weak:
            callback = WeakCallable(callback, *args, **kwargs)
            # We create a callback for weakref destruction for both the
            # signal callback as well as signal data.
            destroy_cb = Callable(self._weakref_destroyed, callback)
            callback.weakref_destroyed_cb = destroy_cb
        else:
            callback = Callable(callback, *args, **kwargs)

        callback._signal_once = once

        if pos == -1:
            pos = len(self._callbacks)

        self._callbacks.insert(pos, callback)
        self._changed(Signal.CONNECTED)

        if self._deferred_args:
            # Clear deferred args before emitting, in case callbacks do emit_deferred().
            deferred_args, self._deferred_args = self._deferred_args, []
            for args, kwargs in deferred_args:
                self.emit(*args, **kwargs)

        return callback


    def connect(self, callback, *args, **kwargs):
        """
        Connects the callback with the (optional) given arguments to be invoked
        when the signal is emitted.

        :param callback: callable invoked when signal emits
        :param args: optional non-keyword arguments passed to the callback
        :param kwargs: optional keyword arguments passed to the callback.
        :return: a new :class:`~kaa.Callable` object encapsulating the supplied
                 callable and arguments.
        """
        return self._connect(callback, args, kwargs)


    def connect_weak(self, callback, *args, **kwargs):
        """
        Weak variant of :meth:`~kaa.Signal.connect` where only weak references are
        held to the callback and arguments.

        :return: a new :class:`~kaa.WeakCallable` object encapsulating the
                 supplied callable and arguments.
        """
        return self._connect(callback, args, kwargs, weak = True)


    def connect_once(self, callback, *args, **kwargs):
        """
        Variant of :meth:`~kaa.Signal.connect` where the callback is automatically
        disconnected after one signal emission.
        """
        return self._connect(callback, args, kwargs, once = True)


    def connect_weak_once(self, callback, *args, **kwargs):
        """
        Weak variant of :meth:`~kaa.Signal.connect_once`.
        """
        return self._connect(callback, args, kwargs, once = True, weak = True)


    def connect_first(self, callback, *args, **kwargs):
        """
        Variant of :meth:`~kaa.Signal.connect` in which the given callback is
        inserted to the front of the callback list.
        """
        return self._connect(callback, args, kwargs, pos = 0)


    def connect_weak_first(self, callback, *args, **kwargs):
        """
        Weak variant of :meth:`~kaa.Signal.connect_first`.
        """
        return self._connect(callback, args, kwargs, weak = True, pos = 0)


    def connect_first_once(self, callback, *args, **kwargs):
        """
        Variant of :meth:`~kaa.Signal.connect_once` in which the given callback is
        inserted to the front of the callback list.
        """
        return self._connect(callback, args, kwargs, once = True, pos = 0)


    def connect_weak_first_once(self, callback, *args, **kwargs):
        """
        Weak variant of :meth:`~kaa.Signal.connect_weak_first_once`.
        """
        return self._connect(callback, args, kwargs, weak = True, once = True, pos = 0)


    def _disconnect(self, callback, args, kwargs):
        assert(callable(callback))
        new_callbacks = []
        for cb in self._callbacks[:]:
            if cb == callback and (len(args) == len(kwargs) == 0 or (args, kwargs) == cb._get_init_args()):
                # This matches what we want to disconnect.
                continue
            new_callbacks.append(cb)

        if len(new_callbacks) != len(self._callbacks):
            self._callbacks = new_callbacks
            self._changed(Signal.DISCONNECTED)
            return True

        return False


    def _changed(self, action):
        """
        Called when a callback was connected or disconnected.

        :param action: kaa.Signal.CONNECTED or kaa.Signal.DISCONNECTED
        """
        if self._changed_cb:
            try:
                self._changed_cb(self, action)
            except CallableError:
                self._changed_cb = None


    def disconnect(self, callback, *args, **kwargs):
        """
        Disconnects the given callback from the signal so that future emissions
        will not invoke that callback any longer.

        If neither args nor kwargs are specified, all instances of the given
        callback (regardless of what arguments they were originally connected with)
        will be disconnected.

        :param callback: either the callback originally connected, or the :class:`~kaa.Callable`
                         object returned by :meth:`~kaa.Signal.connect`.
        :return: True if any callbacks were disconnected, and False if none were found.
        """
        return self._disconnect(callback, args, kwargs)


    def disconnect_all(self):
        """
        Disconnects all callbacks from the signal.
        """
        count = self.count()
        self._callbacks = []
        if self._changed_cb and count > 0:
            self._changed_cb(self, Signal.DISCONNECTED)


    def emit(self, *args, **kwargs):
        """
        Emits the signal, passing the given arguments callback connected to the signal.

        :return: False if any of the callbacks returned False, and True otherwise.
        """
        if len(self._callbacks) == 0:
            return True

        retval = True
        for cb in self._callbacks[:]:
            if cb._signal_once:
                self.disconnect(cb)

            try:
                if cb(*args, **kwargs) == False:
                    retval = False
            except CallableError:
                if self._disconnect(cb, (), {}) != False:
                    # If _disconnect returned False, it means that this callback
                    # wasn't still connected, which almost certainly means that
                    # a weakref was destroyed while we were iterating over the
                    # callbacks in this loop and already disconnected this
                    # callback.  If that's the case, no problem.  However,
                    # if _disconnect returned True, it means that we didn't
                    # expect this callback to become invalid, so reraise.
                    raise
            except Exception, e:
                log.exception('Exception while emitting signal')
        return retval


    def emit_deferred(self, *args, **kwargs):
        """
        Queues the emission until after the next callback is connected.

        This allows a signal to be 'primed' by its creator, and the handler
        that subsequently connects to it will be called with the given
        arguments.
        """
        self._deferred_args.append((args, kwargs))


    def emit_when_handled(self, *args, **kwargs):
        """
        Emits the signal if there are callbacks connected, or defers it until
        the first callback is connected.
        """
        if self.count():
            return self.emit(*args, **kwargs)
        else:
            self.emit_deferred(*args, **kwargs)


    def _weakref_destroyed(self, weakref, callback):
        if CoreThreading.python_shutting_down == False:
            self._disconnect(callback, (), {})


    def count(self):
        """
        Returns the number of callbacks connected to the signal.

        Equivalent to ``len(signal)``.
        """
        return len(self._callbacks)


    def __inprogress__(self):
        """
        Creates an InProgress object representing the signal.

        The InProgress object is finished when this signal is emitted.  The
        InProgress is connected weakly to the signal, so when the InProgress is
        destroyed, the callback is automatically disconnected.

        :return: a new :class:`~kaa.InProgress` object
        """
        from .async import InProgressCallable
        return InProgressCallable(self.connect_weak_once)



class Signals(dict):
    """
    A collection of one or more Signal objects, which behaves like a dictionary
    (with key order preserved).

    The initializer takes zero or more arguments, where each argument can be a:
        * dict (of name=Signal() pairs) or other Signals object
        * tuple/list of (name, Signal) tuples
        * str representing the name of the signal
    """
    def __init__(self, *signals):
        dict.__init__(self)
        # Preserve order of keys.
        self._keys = []
        for s in signals:
            if isinstance(s, dict):
                # parameter is a dict/Signals object
                self.update(s)
                self._keys.extend(s.keys())
            elif isinstance(s, str):
                # parameter is a string
                self[s] = Signal()
                self._keys.append(s)
            elif isinstance(s, (tuple, list)) and len(s) == 2:
                # In form (key, value)
                if isinstance(s[0], basestring) and isinstance(s[1], Signal):
                    self[s[0]] = s[1]
                    self._keys.append(s[0])
                else:
                    raise TypeError('With form (k, v), key must be string and v must be Signal')

            else:
                # parameter is something else, bad
                raise TypeError('signal key must be string')


    def __delitem__(self, key):
        super(Signals, self).__delitem__(key)
        self._keys.remove(key)


    def keys(self):
        """
        List of signal names (strings).
        """
        return self._keys


    def values(self):
        """
        List of Signal objects.
        """
        return [ self[k] for k in self._keys ]


    def __add__(self, signals):
        return Signals(self, *signals)


    def add(self, *signals):
        """
        Creates a new Signals object by merging all signals defined in
        self and the signals specified in the arguments.

        The same types of arguments accepted by the initializer are allowed
        here.
        """
        return Signals(self, *signals)


    def subset(self, *names):
        """
        Returns a new Signals object by taking a subset of the supplied
        signal names.

        The keys of the new Signals object are ordered as specified in the
        names parameter.

            >>> yield signals.subset('pass', 'fail').any()
        """
        return Signals(*[(k, self[k]) for k in names])


    def any(self, finish=None, filter=None):
        """
        Returns an :class:`~kaa.InProgressAny` object with all signals in self.
        """
        from .async import InProgressAny
        return InProgressAny(*self.values(), finish=finish, filter=filter)


    def all(self, finish=None):
        """
        Returns an :class:`~kaa.InProgressAll` object with all signals in self.
        """
        from .async import InProgressAll
        return InProgressAll(*self.values(), finish=finish)


    # XXX: what does this code do?

    def __getattr__(self, attr):
        """
        Get attribute function from Signal().
        """
        if attr.startswith('_') or not hasattr(Signal, attr):
            return getattr(super(Signals, self), attr)
        callback = Callable(self._callattr, attr)
        callback.init_args_first = True
        return callback


    def _callattr(self, attr, signal, *args, **kwargs):
        """
        Call attribute function from Signal().
        """
        return getattr(self[signal], attr)(*args, **kwargs)
