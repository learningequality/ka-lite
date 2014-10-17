# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# main.py - Main loop functions
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

"""
Control the mainloop

This module provides basic functions to control the kaa mainloop.
"""
from __future__ import absolute_import

__all__ = [ 'run', 'stop', 'step', 'select_notifier', 'is_running', 'wakeup',
            'set_as_mainthread', 'is_shutting_down', 'loop', 'signals', 'init',
            'is_initialized' ]

# python imports
import sys
import logging
import os
import time
import signal
import threading
import atexit

from . import nf_wrapper as notifier
from .core import Signals, CoreThreading
from . import timer
from . import thread

# get logging object
log = logging.getLogger('kaa.base.core.main')

# Running state of the main loop.  Possible values are:
#  True: running
#  False: was running, but is now shutdown
#  None: not yet started
_running = None
# Set if currently in shutdown() (to prevent reentrancy)
_shutting_down = False
_shutdown_event = threading.Event()
# Lock preventing multiple threads from executing loop().
_loop_lock = threading.Lock()
# True if init() has been called
_initialized = False

#: mainloop signals to connect to
#:  - init: emitted when kaa.main.init() is invoked; will always be from the 
#           main Python thread
#:  - exception: emitted when an unhandled async exceptions occurs
#:  - step: emitted on each step of the mainloop
#:  - shutdown: emitted on kaa mainloop termination
#:  - shutdown-after: emitted after shutdown signals.
#:  - sigchld: emitted (from notifier loop) when SIGCHLD was received
#:  - exit: emitted when process exits
signals = Signals(
    'init', 'exception', 'shutdown', 'shutdown-after', 'step', 'exit',
    'sigchld'
)


def select_notifier(module, **options):
    log.warning('select_notifier() is deprecated; use kaa.main.init() instead')
    init(module, False, **options)


def init(module=None, reset=False, **options):
    """
    Initialize the Kaa main loop facilities.

    :param module: the main loop implementation to use.

                   * ``generic``: Native python-based main loop (default),
                   * ``gtk``: use pygtk's main loop (automatically selected if
                     the gtk module is imported);
                   * ``twisted``: Twisted main loop;
                   * ``thread``: Native python-based main loop in a separate thread
                     with custom hooks (needs ``handler`` kwarg)
    :type module: str
    :param reset: discards any jobs queued by other threads; this is useful
                  following a fork.
    :param options: module-specific keyword arguments

    This function must be called from the Python main thread.

    .. note::
       Normally it's not necessary to expliticly invoke this function; calling
       loop() or run() will do it for you.  However if you want to use a different
       main loop module than the default, or you begin using the Kaa API in a thread
       before the main loop is started, you will need to invoke init() first.
    """
    global _initialized
    if threading.enumerate()[0] != threading.currentThread():
        # Likely, init() was called implicitly from kaa.main.loop() which in
        # turn was called from a thread.  This can happen if the user calls
        # wait() on an InProgress from within a thread, for example.
        raise RuntimeError('kaa.main.init() must be called explicitly from the Python main thread')

    # catch SIGTERM and SIGINT if possible for a clean shutdown
    def signal_handler(*args):
        # use the preferred stop function for the mainloop. Most
        # backends only call sys.exit(0). Some, like twisted need
        # specific code.
        notifier.shutdown()
    if signal.getsignal(signal.SIGINT) == signal.default_int_handler:
        # But only install our handler if it hasn't been overridden, otherwise
        # we break pdb.
        signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if (module and module != notifier.loaded) or not notifier.loaded:
        if module in ('thread', 'twisted'):
            from . import nf_thread
            nf_thread.init(module, **options)
        else:
            notifier.init(module, **options)

        # TODO: this isn't the right place for this.  It belongs in the
        # notifier init code, but it's not immediately obvious how to best move
        # it there.
        if module and module.startswith('twisted'):
            from twisted.internet.process import reapAllProcesses
            signals['sigchld'].connect(reapAllProcesses)

    CoreThreading.init(signals, reset)
    signals['init'].emit()
    _initialized = True


def loop(condition, timeout=None):
    """
    Executes the main loop until condition is met.

    :param condition: a callable or object that is evaluated after each step
                      of the loop.  If it evaluates False, the loop
                      terminates.  (If condition is therefore ``True``, the
                      loop will run forever.)
    :param timeout: number of seconds after which the loop will terminate
                    (regardless of the condition).

    This function may be called recursively, however two loops may not
    run in parallel threads.

    Generally it is not necessary to call this function.  You probably want
    to use :func:`kaa.main.run` instead.

    .. warning::
       Refer to the warning detailed in :func:`kaa.main.run`.
    """
    with _loop_lock:
        if is_running() and not CoreThreading.is_mainthread():
            # race condition. Two threads started a mainloop and the other
            # one is executed right now. Raise a RuntimeError
            raise RuntimeError('loop running in a different thread')

        initial_mainloop = False
        if not _initialized:
            init()
        if not is_running():
            # no mainloop is running, set this thread as mainloop and
            # set the internal running state.
            initial_mainloop = True
            CoreThreading.set_as_mainthread()
            _set_running(True)


    if not callable(condition):
        condition = lambda: condition

    abort = []
    if timeout is not None:
        # timeout handling to stop the mainloop after the given timeout
        # even when the condition is still True.
        sec = timeout
        timeout = timer.OneShotTimer(lambda: abort.append(True))
        timeout.start(sec)

    try:
        while condition() and not abort:
            try:
                notifier.step()
                signals['step'].emit()
            except BaseException, e:
                if signals['exception'].emit(*sys.exc_info()) != False:
                    # Either there are no global exception handlers, or none of
                    # them explicitly returned False to abort mainloop
                    # termination.  So abort the main loop.
                    type, value, tb = sys.exc_info()
                    raise type, value, tb
    finally:
        # make sure we set mainloop status
        if timeout is not None:
            timeout.stop()
        if initial_mainloop:
            _set_running(False)


def run(threaded=False, daemon=True):
    """
    Start the main loop.

    The main loop will continue to run until an exception is raised
    (and makes its way back up to the main loop without being caught).
    SystemExit and KeyboardInterrupt exceptions will cause the main loop
    to terminate, and execution will resume after run() was called.

    :param threaded: if True, the Kaa mainloop will start in a new thread.
    :type threaded: bool
    :param daemon: applies when ``threaded=True``, and indicates if the thread
                   running the main loop is a daemon thread.  Daemon threads will
                   not block the program from exiting when the main Python thread
                   terminates.

    Specifying ``threaded=True`` is useful if the main Python thread has been
    co-opted by another mainloop framework and you want to use Kaa in parallel.
    Another use-case would be using kaa from the interactive Python shell::

        >>> import kaa, sys, time
        >>> kaa.main.run(threaded=True)
        >>> @kaa.threaded()
        ... def foo():
        ...     time.sleep(5)
        ...     return 'Background task finished\\n'
        ...
        >>> foo().connect(sys.stdout.write)
        <Callable for <built-in method write of file object at 0xb7de5068>>
        >>> Background task finished

    .. warning::

       Once the main loop has been started, do not fork using :func:`os.fork`.
       Doing so may cause peculiar interactions when using threads.  To safely
       fork, use :func:`kaa.utils.fork`, which may be called whether the main
       loop has been started or not.
    """
    if is_running():
        raise RuntimeError('Main loop is already running')

    if threaded:
        # init() gets called in loop() too (which we call later), but we need
        # to call it now before we restart within a new thread.
        init()
        # start mainloop as thread and wait until it is started
        event = threading.Event()
        timer.OneShotTimer(event.set).start(0)
        t = threading.Thread(target=run, name='kaa mainloop')
        t.setDaemon(daemon)
        t.start()
        return event.wait()

    global _shutting_down
    _shutting_down = False
    _shutdown_event.clear()

    try:
        loop(True)
    except (KeyboardInterrupt, SystemExit):
        try:
            # This looks stupid, I know that. The problem is that if we have
            # a KeyboardInterrupt, that flag is still valid somewhere inside
            # python. The next system call will fail because of that. Since we
            # don't want a join of threads or similar fail, we use a very short
            # sleep here. In most cases we won't sleep at all because this sleep
            # fails. But after that everything is back to normal.
            # XXX: (tack) this sounds like an interpreter bug, does it still do this?
            time.sleep(0.001)
        except:
            pass
    finally:
        # _stop might be None if mainloop was run in a daemon thread.  In that
        # case, we get here when the interpreter is shutting down, and we've
        # shutdown enough that stop no longer exists.  It doesn't matter,
        # because the atexit handler will have called stop already.
        if _stop:
            _stop()



def stop():
    """
    Stop the main loop and terminate all child processes and thread
    pools started via the Kaa API.

    Any notifier callback can also cause the main loop to terminate
    by raising SystemExit.
    """
    # Put the public stop() in a timer to ensure we unravel the stack before
    # shutting down the notifier.
    #
    # notifier.shutdown() raises SystemExit which could get caught and handled in
    # undesirable ways by something else and the notifier loop may never even see
    # it.
    #
    # Previous versions decorated stop() with @timed but this prevented stop()
    # from being executed more than one time (i.e. main loop being
    # started/stopped after previously being started/stopped).  With
    # @timed(POLICy_ONCE), a single OneShotTimer was created and attached to
    # this function.  But because _stop() raises SystemExit, the timer never
    # got unregistered and subsequent invocations of stop() assumed the timer
    # was still running and turned the call into a no-op.
    timer.OneShotTimer(_stop).start(0)


def _stop():
    """
    Internal function to shutdown the main loop.  This is called by stop()
    (via a timer) and by run() when the notifier loop actually stops.  The
    flow looks like:
        1. user calls stop()
        2. a one-shot timer is scheduled for _stop()
        3. bext iteration of main loop, _stop() is called.
        4. _shutting_down == False and is_running() == True, so
           notifier.shutdown() is invoked.
        5. notifier.shutdown() raises SystemExit which aborts _stop() and
           is caught by the notifier loop.
        6. notifier loop() returns
        7. 'finally' block in run() invokes _stop()
        8. _shutting_down == False and is_running() == False, so we set
           _shutting_down = True and proceed with cleanup.
        9. set the _shutdown_event so anyway threads waiting in
           _shutdown_check() can resume.
    """
    global _shutting_down

    if _shutting_down:
        return

    if is_running():
        # loop still running, send system exit
        log.info('Stop notifier loop')
        notifier.shutdown()

    _shutting_down = True
    
    signals["shutdown"].emit()
    signals["shutdown"].disconnect_all()
    signals["step"].disconnect_all()

    # Process.supervisor.stopall() is attached to shutdown-after.  We emit this
    # after 'shutdown' so that callbacks connected to 'shutdown' get a chance
    # to terminate any processes.
    signals['shutdown-after'].emit()

    thread.killall()
    # One final attempt to reap any remaining zombies
    try:
        os.waitpid(-1, os.WNOHANG)
    except OSError:
        pass
    _shutdown_event.set()


def step(*args, **kwargs):
    """
    Performs a single iteration of the main loop.

    .. warning::

       This function should almost certainly never be called directly.  Use it
       at your own peril.  (If you do use it, you must call
       :func:`~kaa.main.init` first.)
    """
    if not CoreThreading.is_mainthread():
        # If step is being called from a thread, wake up the mainthread
        # instead of allowing the thread into notifier.step.
        CoreThreading.wakeup()
        # Sleep for epsilon to prevent busy loops.
        time.sleep(0.001)
        return
    notifier.step(*args, **kwargs)
    signals['step'].emit()


def is_initialized():
    """
    Return True if init() was called.
    """
    return _initialized


def is_running():
    """
    Return True if the main loop is currently running.
    """
    return _running == True


def is_shutting_down():
    """
    Return True if the main loop is currently inside stop()
    """
    return _shutting_down


def is_stopped():
    """
    Returns True if the main loop used to be running but is now shutdown.

    This is useful for worker tasks running a thread that need to live for
    the life of the application, but are started before kaa.main.run() is
    called.  These threads can loop until kaa.main.is_stopped()
    """
    return _running == False


# Expose some of the CoreThreading functions in the main namespace for public
# consumption.
wakeup = CoreThreading.wakeup
is_mainthread = CoreThreading.is_mainthread
set_as_mainthread = CoreThreading.set_as_mainthread


def _set_running(status):
    """
    Set mainloop running status.
    """
    global _running
    _running = status


def _shutdown_check(*args):
    # Helper function to shutdown kaa on system exit
    # The problem is that pytgtk just exits python and
    # does not simply return from the main loop and kaa
    # can't call the shutdown handler. This is not a perfect
    # solution, e.g. with the generic mainloop you can do
    # stuff after kaa.main.run() which is not possible with gtk
    if is_running():
        # If the kaa mainthread (i.e. thread the mainloop is running in)
        # is not the program's main thread, then is_mainthread() will be False
        # and we don't need to set running=False since shutdown() will raise a
        # SystemExit and things will exit normally.
        if CoreThreading.is_mainthread():
            _set_running(False)
        _stop()
        if not CoreThreading.is_mainthread():
            # Main loop is running in another thread, so we need to wait for it
            # to finish.
            _shutdown_event.wait()


# check to make sure we really call our shutdown function
atexit.register(_shutdown_check)
atexit.register(signals['exit'].emit)
