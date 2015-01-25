# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# thread.py - Thread support for the Kaa Framework
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

__all__ = [
    'MainThreadCallable', 'ThreadCallable', 'threaded', 'MAINTHREAD',
    'synchronized', 'ThreadInProgress', 'ThreadPool', 'register_thread_pool',
    'get_thread_pool'
]

# python imports
import sys
import threading
import logging
import socket
import errno
import types
import time
import ctypes
from thread import LockType

# kaa imports
from .callable import Callable
from . import nf_wrapper as notifier
from .utils import wraps, DecoratorDataStore, property
from .core import CoreThreading, Object
from .async import InProgress, InProgressAborted, InProgressStatus

# get logging object
log = logging.getLogger('kaa.base.core.thread')

# Thread pool name -> ThreadPool object
_thread_pools = {}

# For threaded decorator
MAINTHREAD = object()

def killall():
    """
    Kill all running job server. This function will be called by the main
    loop when it shuts down.
    """
    for pool in _thread_pools.values():
        for thread in pool._members:
            thread.stop()
            thread.join()


def register_thread_pool(name, pool):
    """
    Registers a :class:`~kaa.ThreadPool` under the given name.

    :param name: the name under which to register this thread pool
    :type name: str
    :param pool: the thread pool object
    :type pool: :class:`~kaa.ThreadPool`
    :returns: the supplied :class:`~kaa.ThreadPool` object

    Once registered, the thread pool may be referenced by name when using the
    :func:`@kaa.threaded() <kaa.threaded>` decorator or
    :class:`~kaa.ThreadPoolCallable` class.

    Thread pool names are arbitrary strings, but the recommended convention
    is to format the pool name as ``appname::poolname``, where ``appname``
    uniquely identifies the application, and ``poolname`` describes the purpose
    of the thread pool.  An example might be ``beacon::thumbnailer``.
    """
    if name in _thread_pools:
        raise ValueError('A registered pool already exists with name "%s"' % name)
    assert(isinstance(pool, ThreadPool))
    _thread_pools[name] = pool
    pool._rename(name)
    return pool


def get_thread_pool(name):
    """
    Returns the :class:`~kaa.ThreadPool` previously registered with the given
    name, or None if no :class:`~kaa.ThreadPool` was registered with that name.
    """
    return _thread_pools.get(name)


class MainThreadCallable(Callable):
    """
    Wraps a callable and ensures it is invoked from the main thread.
    """
    def __call__(self, *args, **kwargs):
        in_progress = InProgress()

        if CoreThreading.is_mainthread():
            try:
                result = super(MainThreadCallable, self).__call__(*args, **kwargs)
            except BaseException, e:
                # All exceptions, including SystemExit and KeyboardInterrupt,
                # are caught and thrown to the InProgress, because it may be
                # waiting in another thread.  However SE and KI are reraised
                # in here the main thread so they can be propagated back up
                # the mainloop.
                in_progress.throw()
                if isinstance(e, (KeyboardInterrupt, SystemExit)):
                    raise
            else:
                in_progress.finish(result)

            return in_progress

        CoreThreading.queue_callback(self, args, kwargs, in_progress)

        # Return an InProgress object which the caller can connect to
        # or wait on.
        return in_progress


class ThreadInProgress(InProgress):
    """
    An :class:`~kaa.InProgress` class that represents threaded tasks.  You will
    likely not need to instantiate this class directly, but ``ThreadInProgress``
    objects are returned when invoking :class:`~kaa.ThreadCallable` or
    :class:`~kaa.ThreadPoolCallable` objects, or functions decorated with
    :func:`@kaa.threaded() <kaa.threaded>`.

    Callbacks connected to this InProgress are invoked from the main thread.
    """
    def __init__(self, func, *args, **kwargs):
        super(ThreadInProgress, self).__init__()
        self._callable = Callable(func, *args, **kwargs)
        # The Thread object the callback is running in.
        self._thread = None


    def __call__(self, *args, **kwargs):
        """
        Execute the wrapped callable.
        """
        if self.finished:
            # We're finished before we even started.  The only sane reason for
            # this is that the we were aborted, so check for for this, and if
            # it's not the case, log an error.
            if self.failed and self._exception[0] == InProgressAborted:
                # Aborted, fine.
                return

            # This shouldn't happen.  If it does, it's certainly an error
            # condition.  But as we are inside the thread now and already
            # finished, we can't really raise an exception.  So logging the
            # error will have to suffice.
            log.error('Attempting to start thread which has already finished')

        if self._callable is None:
            # Attempting to invoke multiple times?  Shouldn't happen.
            return None

        self._thread = threading.currentThread()  # for abort()
        try:
            result = self._callable()
            # Kludge alert: InProgressAborted gets raised asynchronously inside
            # the thread.  Assuming it doesn't inadvertently get cleared out
            # by PyErr_Clear(), it may take up to check-interval ticks for
            # it to trigger.  So we do a dummy loop to chew up that many ticks
            # (roughly) to cause any pending async InProgressAborted to raise
            # here, which we'll catch next.  The overhead added by this loop is
            # negligible.  [About 10us on my system.]  It has been empirically
            # determined that each pass of the loop consumes a tick.  (We end
            # up consuming a few more for loop setup / teardown.)
            for i in xrange(sys.getcheckinterval()):
                pass
        except InProgressAborted:
            # InProgressAborted was raised inside the thread (from the InProgress
            # abort handler).  This means we're already finished, so there's no
            # need to do anything further.
            pass
        except:
            # XXX: should we really be catching KeyboardInterrupt and SystemExit?
            MainThreadCallable(self.throw)(*sys.exc_info())
        else:
            if type(result) == types.GeneratorType or isinstance(result, InProgress):
                # Looks like the callable is yielding something, or callable is a
                # coroutine-decorated function.  Not supported (yet?).  In the
                # case of coroutines, the first entry will execute in the
                # thread, but subsequent entries (via the generator's next())
                # will be from the mainthread, which is almost certainly _not_
                # what is intended by threading a coroutine.
                log.warning('NYI: coroutines cannot (yet) be executed in threads.')

            # If we're finished, it means we were aborted, but probably caught the
            # InProgressAborted inside the threaded callable.  If so, we discard the
            # return value from the callable, as we're considered finished.  Otherwise
            # finish up in the mainthread.
            if not self.finished:
                MainThreadCallable(self.finish)(result)

        self._thread = None
        self._callable = None


    @property
    def active(self):
        """
        True if the callable is still waiting to be processed.
        """
        return self._callable is not None


    def abort(self, exc=None):
        """
        Aborts the callable being executed inside a thread.  (Or attempts to.)

        See :meth:`kaa.InProgress.abort` for argument details.

        Invocation of a :class:`~kaa.ThreadCallable` or
        :class:`~kaa.ThreadPoolCallable` will return a ``ThreadInProgress``
        object which may be aborted by calling this method.  When an
        in-progress thread is aborted, an :class:`~kaa.InProgressAborted`
        exception is raised inside the thread.

        Just prior to raising :class:`~kaa.InProgressAborted` inside the thread, the
        :attr:`~ThreadCallable.signals.abort` signal will be emitted.
        Callbacks connected to this signal are invoked within the thread from
        which ``abort()`` was called.  If any of the callbacks return
        ``False``, :class:`~kaa.InProgressAborted` will not be raised in the thread.

        It is possible to catch :class:`~kaa.InProgressAborted` within the
        thread to deal with cleanup, but any return value from the threaded
        callable will be discarded.  It is therefore not possible abort an
        abort within the thread itself.  However, if the InProgress is aborted
        before the thread has a chance to start, the thread is not started at
        all, and so obviously the threaded callable will not receive
        :class:`~kaa.InProgressAborted`.

        .. warning::

           This method raises an exception asynchronously within the thread,
           and this is unreliable.  The asynchronous exception may get
           inadvertently cleared internally, and if it doesn't, it will in any
           case take up to 100 ticks for it to trigger within the thread.

           A tick is one or more Python VM bytecodes, which means that if the
           thread is currently executing non-CPython C code, the thread cannot
           be interrupted.  The worst case scenario would be a blocking system
           call, which cannot be reliably interrupted when running inside a
           thread.

           This approach still has uses as a general-purposes aborting
           mechanism, but, if possible, it is preferable for you to implement
           custom logic by attaching an abort handler to the
           :class:`~kaa.ThreadCallable` or :class:`~kaa.ThreadPoolCallable`
           object.
        """
        return super(ThreadInProgress, self).abort(exc)


class ThreadCallableBase(Callable, Object):
    __kaasignals__ = {
        'abort':
            '''
            Emitted when the threaded callable is aborted.

            .. describe:: def callback()

               This callback takes no arguments

            See :meth:`~ThreadInProgress.abort` for a more detailed discussion.

            Handlers may return False to prevent
            :class:`~kaa.InProgressAborted` from being raised inside the
            thread.  However, the ThreadInProgress is still considered aborted
            regardless.  Handlers of this signal are intended to implement more
            appropriate logic to cancel the threaded callable.
            '''
    }

    def _setup_abort(self, inprogress):
        # Hook an abort callback for this ThreadInProgress.
        def abort(exc):
            if not inprogress._thread:
                # Already stopped or never ran.
                return

            if self.signals['abort'].emit(exc) == False:
                # A callback returned False, do not raise inside thread.
                return

            # This magic uses Python/C to raise an exception inside the thread.
            if hasattr(inprogress._thread, 'ident'):
                tid = inprogress._thread.ident
            else:
                tids = [tid for tid, tobj in threading._active.items() if tobj == inprogress._thread]
                if not tids:
                    # Thread not found.  It must already have finished.
                    return
                tid = tids[0]

            # We can't raise the exact exception into the thread, so just use the class.
            res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(exc.__class__))
            if res == 0:
                # Thread not found.  Must have terminated an instant ago.
                return

            # FIXME: It's possible for the InProgressAborted exception to get swallowed
            # by PyErr_Clear() somewhere in the thread.  We could use a timer to keep
            # raising the exception inside the thread until it dies.

        inprogress.signals['abort'].connect(abort)



class ThreadCallable(ThreadCallableBase):
    """
    A special :class:`~kaa.Callable` used to execute a function or method
    inside a thread.  A new thread is created each time the ThreadCallable is
    invoked.
    """
    _wait_on_exit = True

    @property
    def wait_on_exit(self):
        """
        If True (default), wait for the thread on application exit.

        If False, this causes the thread to be a so-called "daemon thread."  A
        Python program exits when no non-daemon threads are left running.

        .. warning::

           If the main loop is not running (via :func:`kaa.main.run`) it is
           recommended this not be set to ``False``, otherwise you may experience
           intermittent exceptions during interpreter shutdown.
        """
        return self._wait_on_exit

    @wait_on_exit.setter
    def wait_on_exit(self, wait):
        self._wait_on_exit = wait


    def _create_thread(self, *args, **kwargs):
        """
        Create and start the thread.
        """
        cb = Callable._get_func(self)
        async = ThreadInProgress(cb, *args, **kwargs)
        # create thread and setDaemon
        t = threading.Thread(target=async)
        t.setDaemon(not self._wait_on_exit)
        # connect thread.join to the InProgress
        join = lambda *args, **kwargs: t.join()

        # Hook the aborted signal for the ThreadInProgress to stop the threaded
        # callable.
        self._setup_abort(async)
        # XXX: this was in the original abort code but I don't think it's necessary.
        # If I'm wrong, uncomment and explain why it's needed.
        #async.signals['abort'].connect(lambda: async.exception.disconnect(join))

        async.connect_both(join, join)
        # start the thread
        t.start()
        return async


    def _get_func(self):
        """
        Return callable for this Callback.
        """
        return self._create_thread



class ThreadPoolCallable(ThreadCallableBase):
    """
    A special :class:`~kaa.Callable` used to execute a function or method
    inside a thread as part of a thread pool.  If all threads in the thread
    pool are busy, it is queued and will be invoked when one of the threads
    become available.
    """
    def __init__(self, poolinfo, func, *args, **kwargs):
        """
        :param poolinfo: a :class:`~kaa.ThreadPool` object or name of a previously
                         registered thread pool, or a 2-tuple (``pool``, ``priority``),
                         where ``pool`` is a :class:`~kaa.ThreadPool` object or registered
                         name, and ``priority`` is the integer priority that controls
                         where in the queue the job will be placed.
        :param func: the underlying callable that will be called from within a
                     thread.
        """
        super(ThreadPoolCallable, self).__init__(func, *args, **kwargs)
        if isinstance(poolinfo, (list, tuple)):
            self._pool, self.priority = poolinfo
        else:
            self._pool, self.priority = poolinfo, 0

        if not isinstance(self._pool, ThreadPool):
            try:
                self._pool = _thread_pools[self._pool]
            except KeyError:
                log.warning('Implicitly registering thread pool "%s"; use register_thread_pool() instead',
                            self._pool)
                self._pool = register_thread_pool(self._pool, ThreadPool())


    def _create_job(self, *args, **kwargs):
        cb = super(ThreadPoolCallable, self)._get_func()
        job = self._pool.enqueue(ThreadInProgress(cb, *args, **kwargs), self.priority)
        # Hook the aborted signal for the ThreadInProgress to stop the thread
        # callback.
        if job:
            self._setup_abort(job)
        return job


    def _get_func(self):
        return self._create_job



class _ThreadPoolMember(threading.Thread):
    """
    Member thread for thread pools.  This class dips its fingers into
    ThreadPool private members.
    """
    def __init__(self, pool, name):
        super(_ThreadPoolMember, self).__init__(name=name)
        self.setDaemon(True)
        self.stopped = False
        self.pool = pool
        log.debug('thread pool member "%s" starting', name)
        self.start()


    def stop(self):
        """
        Stop the thread.
        """
        self.pool._condition.acquire()
        self.stopped = True
        self.pool._condition.notify()
        self.pool._condition.release()


    def _exit(self):
        try:
            self.pool._members.remove(self)
        except ValueError:
            # We were stopped by the pool, which removed us already.
            pass
        log.debug('thread pool member "%s" exited', self.getName())


    def run(self):
        """
        Thread main function.
        """
        while not self.stopped:
            # get a new job to process
            self.pool._condition.acquire()
            t0 = time.time()
            while not self.pool._queue and not self.stopped:
                # nothing to do, wait
                self.pool._condition.wait(self.pool._timeout - (time.time() - t0))
                if time.time() - t0 >= self.pool._timeout:
                    # Timeout waiting for a job, exit.
                    self.pool._condition.release()
                    return self._exit()

            if self.stopped:
                self.pool._condition.release()
                return self._exit()

            job = self.pool._queue.pop(0)
            self.pool._busy += 1
            self.pool._condition.release()
            job()
            self.pool._busy -= 1

        self._exit()


class ThreadPool(object):
    """
    Manages a pool of one or more threads for use with the
    :func:`@kaa.threaded() <kaa.threaded>` decorator, or
    :class:`~kaa.ThreadPoolCallable` objects.

    ThreadPool objects may be assigned a name by calling
    :func:`kaa.register_thread_pool`.  When done, the name can be referenced
    instead of passing the ThreadPool object.
    """
    def __init__(self, size=1):
        """
        :param size: maximum number of threads this thread pool will grow to.
        :type size: int
        """
        self._size = size
        # List of ThreadPoolMember objects for this thread pool.
        self._members = []
        # Shared condition for all pool members
        self._condition = threading.Condition()
        # Shared work queue of 2-tuples (callback, priority)
        self._queue = []
        # Shared thread timeout.
        self._timeout = 30
        # Thread pool name.  Set using register_thread_pool()
        self._name = None
        # Number of pool members that are busy.
        self._busy = 0


    def __repr__(self):
        if not self._name:
            return '<Anonymous ThreadPool object at 0x%x>' % id(self)
        else:
            return '<ThreadPool "%s" object at 0x%x>' % (self._name, id(self))


    def _resize(self):
        """
        Grows or shrinks pool members based on current number of jobs and
        size limits.
        """
        while len(self._members) - self._busy < len(self._queue) and len(self._members) < self._size:
            # We have jobs waiting and slots free, so spawn new members.
            member = _ThreadPoolMember(self, '%s#%d' % (self._name, len(self._members)+1))
            self._members.append(member)

        while len(self._members) > self._size:
            # Too many pool members.
            # TODO: rather than indiscriminantly removing the last member,
            # first try to remove any that aren't processing jobs.
            self._members.pop().stop()


    def enqueue(self, callback, priority=0):
        """
        Creates a job from the given callback and adds it to the thread pool
        work queue.

        :param callback: a callable which will be invoked inside one of the
                         pool threads.
        :type callback: callable
        :param priority: determines the relative priority of the job; higher
                         values are higher priority.
        :type priority: int
        :returns: a :class:`~kaa.ThreadInProgress` object for this job.

        It should generally not be necessary to call this method directly.
        It is called implicitly when using the :func:`@kaa.threaded() <kaa.threaded>`
        decorator, or :class:`~kaa.ThreadPoolCallable` objects.
        """
        if not isinstance(callback, ThreadInProgress):
            callback = ThreadInProgress(callback)

        callback.priority = priority

        self._condition.acquire()
        self._queue.append(callback)
        self._queue.sort(key=lambda job: job.priority, reverse=True)
        self._resize()
        self._condition.notify()
        self._condition.release()
        return callback


    def dequeue(self, job):
        """
        Removes the given job from the thread queue.

        :param job: the job as returned by :meth:`~kaa.ThreadPool.enqueue`
        :type job: :class:`~kaa.ThreadInProgress` object
        :returns: True if the job existed and was removed, and False if the
                  job was not found.
        """
        self._condition.acquire()
        try:
            self._queue.remove(job)
        except ValueError:
            found = False
        else:
            found = True
        self._condition.release()
        return found


    @property
    def size(self):
        """
        The maxium number of threads this pool may grow to.

        If this value is increased and jobs are waiting to be processed, new
        threads will be spawned as needed (but will not exceed the limit).

        If this value is decreased and there are too many active pool members
        as a result, the necessary number of pool members will be stopped.  If
        those members are currently processing jobs, they will exit once the job
        is complete.
        """
        return self._size

    @size.setter
    def size(self, value):
        self._size = value
        self._resize()


    @property
    def timeout(self):
        """
        Number of seconds a thread pool member will wait for a job before stopping.

        A thread which stopped due to timeout may be restarted if new jobs are
        enqueued that would put that thread to work.
        """
        return self._timeout


    @timeout.setter
    def timeout(self, value):
        self._condition.acquire()
        do_notify = value < self._timeout
        self._timeout = value
        if do_notify:
            # We reduced the timeout value, so wakeup all threads so they can
            # decide if they've been waiting too long for a new job.
            self._condition.notifyAll()
        self._condition.release()


    @property
    def name(self):
        """
        The name under which this thread pool was registered.

        Thread pools are registered via :func:`kaa.register_thread_pool`.  Once
        registered, the thread pool may subsequently be referenced by name when
        using :class:`~kaa.ThreadPoolCallable` or the
        :func:`@kaa.threaded() <kaa.threaded>` decorator.

        An ThreadPool which has not been registered is called an anonymous thread
        pool, and may be passed directly to :func:`@kaa.threaded() <kaa.threaded>`
        and :class:`~kaa.ThreadPoolCallable`.
        """
        return self._name


    def _rename(self, name):
        # This is called by register_thread_pool().
        self._condition.acquire()
        self._name = name
        for member in self._members:
            member.name = self._name
        self._condition.release()



def threaded(pool=None, priority=0, async=True, progress=False, wait=False):
    """
    Decorator causing the decorated function to be executed within a thread
    when invoked.

    :param pool: a :class:`~kaa.ThreadPool` object or name of a registered
                 thread pool; if None, a new thread will be created for each
                 invocation.
    :type pool: :class:`~kaa.ThreadPool`, str, :const:`kaa.MAINTHREAD`, or None
    :param priority: priority for the job in the thread pool
    :type priority: int
    :param async: if False, blocks until the decorated function completes
    :type async: bool
    :param progress: if True, the first argument passed to the decorated function
                     will be an :class:`~kaa.InProgressStatus` object in order
                     to indicate execution progress to the caller.
    :type progress: bool
    :param wait: corresponds to :attr:`kaa.ThreadCallable.wait_on_exit`.  It may
                 be necessary to set this to True if the kaa main loop is not
                 running.  (Default: False)
    :type wait: bool
    :returns: :class:`~kaa.ThreadedInProgress` if ``async=False``, or the return value
              or the decorated function if ``async=True``

    A special pool constant :const:`kaa.MAINTHREAD` is available, which causes
    the decorated function to always be invoked from the main thread.  In this
    case, currently the ``priority`` argument is ignored.

    If ``pool`` is None, the decorated function will be wrapped in a
    :class:`~kaa.ThreadCallable` for execution.  Otherwise, ``pool`` specifies
    either a :class:`~kaa.ThreadPool` object or pool name previously registered
    with :func:`kaa.register_thread_pool`, and the decorated function will be
    wrapped in a :class:`~kaa.ThreadPoolCallable` for execution.
    """
    if progress is True:
        progress = InProgressStatus

    def decorator(func):
        args = (progress(),) if progress else ()
        if pool == MAINTHREAD:
            callback = MainThreadCallable(func, *args)
        elif pool:
            callback = ThreadPoolCallable((pool, priority), func, *args)
        else:
            callback = ThreadCallable(func, *args)
            callback.wait_on_exit = wait

        @wraps(func, lshift=int(not not progress))
        def newfunc(*args, **kwargs):
            if pool == MAINTHREAD and not async and CoreThreading.is_mainthread():
                # Fast-path case: mainthread synchronous call from the mainthread
                return func(*args, **kwargs)

            # callback will always return InProgress
            in_progress = callback(*args, **kwargs)
            if not async:
                return in_progress.wait()
            if progress:
                in_progress.progress = callback._args[0]
            return in_progress

        # Boilerplate for @kaa.generator
        newfunc.decorator = threaded
        newfunc.origfunc = func
        newfunc.redecorate = lambda: threaded(pool, priority, async, progress)
        return newfunc

    return decorator


class synchronized(object):
    """
    synchronized decorator and `with` statement similar to synchronized
    in Java. When decorating a non-member function, a lock or any class
    inheriting from object may be provided.

    :param obj: object were all calls should be synchronized to.
      if not provided it will be the object for member functions
      or an RLock for functions.
    """
    def __init__(self, obj=None):
        """
        Create a synchronized object. Note: when used on classes a new
        member _kaa_synchronized_lock will be added to that class.
        """
        if obj is None:
            # decorator in classes
            self._lock = None
            return
        if isinstance(obj, (threading._RLock, LockType)):
            # decorator from functions
            self._lock = obj
            return
        # with statement or function decorator with object
        if not hasattr(obj, '_kaa_synchronized_lock'):
            obj._kaa_synchronized_lock = threading.RLock()
        self._lock = obj._kaa_synchronized_lock

    def __enter__(self):
        """
        with statement enter
        """
        if self._lock is None:
            raise RuntimeError('synchronized in with needs a parameter')
        self._lock.acquire()
        return self._lock

    def __exit__(self, type, value, traceback):
        """
        with statement exit
        """
        self._lock.release()
        return False

    def __call__(self, func):
        """
        decorator init
        """
        def call(*args, **kwargs):
            """
            decorator call
            """
            lock = self._lock
            if lock is None:
                # Lock not specified, use one attached to decorated function.
                store = DecoratorDataStore(func, call, args)
                if 'synchronized_lock' not in store:
                    store.synchronized_lock = threading.RLock()
                lock = store.synchronized_lock

            lock.acquire()
            try:
                return func(*args, **kwargs)
            finally:
                lock.release()
        return call
