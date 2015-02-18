# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# timer.py - Timer classes for the main loop
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

__all__ = [ 'timed', 'Timer', 'WeakTimer', 'OneShotTimer', 'WeakOneShotTimer',
            'AtTimer', 'OneShotAtTimer', 'delay', 'POLICY_ONCE', 'POLICY_MANY',
            'POLICY_RESTART' ]

import logging
import datetime

from .weakref import weakref
from .utils import wraps, DecoratorDataStore, property
from . import nf_wrapper as notifier
from .core import CoreThreading
from . import thread
# Needed for delay(); thread module needs async anyway, so we won't avoid a
# circular dependency by moving delay() (back) into async.py
from .async import InProgressCallable

POLICY_ONCE = 'once'
POLICY_MANY = 'many'
POLICY_RESTART = 'restart'

# get logging object
log = logging.getLogger('kaa.base.core.timer')


def timed(interval, timer=None, policy=POLICY_MANY):
    """
    Decorator to call the decorated function in a Timer. When calling the
    function, a timer will be started with the given interval calling that
    function.  The decorated function will be called from the main thread.

    The timer parameter optionally specifies which timer class should be
    used to wrap the function.  kaa.Timer (default) or kaa.WeakTimer will
    repeatedly invoke the decorated function until it returns False.
    kaa.OneShotTimer or kaa.WeakOneShotTimer will invoke the function once,
    delaying it by the specified interval.  (In this case the return value
    of the decorated function is irrelevant.)

    The policy parameter controls how multiple invocations of the decorated
    function should be handled.  By default (POLICY_MANY), each invocation of
    the function will create a new timer, each firing at the specified
    interval.  If policy is POLICY_ONCE, subsequent invocations are ignored
    while the first timer is still active.  If the policy is POLICY_RESTART,
    subsequent invocations will restart the first timer.

    Note that in the case of POLICY_ONCE or POLICY_RESTART, if the timer is
    currently running, any arguments passed to the decorated function on
    subsequent calls will be discarded.
    """
    if not policy in (POLICY_MANY, POLICY_ONCE, POLICY_RESTART):
        raise ValueError('Invalid @kaa.timed policy %s' % policy)

    def decorator(func):
        @wraps(func)
        def newfunc(*args, **kwargs):
            if policy == POLICY_MANY:
                # just start the timer
                t = (timer or Timer)(func, *args, **kwargs)
                t.start(interval)
                return True
            store = DecoratorDataStore(func, newfunc, args)
            # check current timer
            if 'timer' in store and store.timer and store.timer.active:
                if policy == POLICY_ONCE:
                    # timer already running and not override
                    return False
                # stop old timer
                store.timer.stop()
            # create new timer, store it in the object and start it
            t = (timer or Timer)(func, *args, **kwargs)
            store.timer = weakref(t)
            t.start(interval)
            return True
        return newfunc

    return decorator


def delay(seconds):
    """
    Returns an InProgress that finishes after the given time in seconds.

    :param obj: object to represent as an InProgress.
    :return: :class:`~kaa.InProgress`
    """
    ip = InProgressCallable()
    t = OneShotTimer(ip)
    # If the IP gets aborted, stop the timer.  Otherwise the timer
    # will fire and the IP would attempt to get finished a second
    # time (and would therefore raise an exception).
    ip.signals['abort'].connect_weak(lambda exc: t.stop())
    t.start(seconds)
    return ip


class Timer(notifier.NotifierCallback):
    """
    Invokes the supplied callback after the supplied interval (passed to
    :meth:`~kaa.Timer.start`) elapses.  The Timer is created stopped.

    When the timer interval elapses, we say that the timer is "fired" or
    "triggered," at which time the given callback is invoked.

    If the callback returns False, then the timer is automatically stopped.
    If it returns any other value (including None), the timer will continue
    to fire.
    """

    __interval = None

    def __init__(self, callback, *args, **kwargs):
        """
        :param callback: the callable to be invoked
        :param args: the arguments to be passed to the callable when it's invoked
        :param kwargs: the keyword arguments to be passed to the callable when it's invoked
        """
        super(Timer, self).__init__(callback, *args, **kwargs)
        self.restart_when_active = True


    @thread.threaded(thread.MAINTHREAD)
    def start(self, interval, now=False):
        """
        Start the timer, invoking the callback every *interval* seconds.

        :param interval: interval between invocations of the callback, in seconds
        :type interval: float
        :param now: if True, invoke the callback once immediately before starting
                    the timer.
        :type now: bool

        If the timer is already running, it is stopped and restarted with
        the given interval.  The timer's precision is at the mercy of other
        tasks running in the main loop.  For example, if another task
        (a different timer, or I/O callback) blocks the mainloop for longer
        than the given timer interval, the callback will be invoked late.

        This method may safely be called from a thread, however the timer
        callback will be invoked from the main thread.
        """
        if self.active:
            if not self.restart_when_active:
                return
            self.unregister()
        if now:
            self()
        self._id = notifier.timer_add(int(interval * 1000), self)
        self.__interval = interval


    @property
    def interval(self):
        """
        Timer interval when the timer is running, None if not.  The interval
        cannot be changed once the timer is started, and it is set via the
        :meth:`~kaa.Timer.start` method.
        """
        return self.__interval


    @thread.threaded(thread.MAINTHREAD)
    def stop(self):
        """
        Stop a running timer.

        This method is a no-op if the timer is already stopped.  It may also be
        called from a thread, however if the timer callback is currently
        executing in the main thread, it will of course have to finish, but it
        will not be called again unless the timer is restarted.
        """
        self.unregister()


    def unregister(self):
        """
        Removes the timer from the notifier.

        This is considered an internal function (required to be implemented by
        subclasses of NotifierCallback).  User should use stop() instead.
        """
        if self.active:
            notifier.timer_remove(self._id)
            super(Timer, self).unregister()
        self.__interval = None



class WeakTimer(notifier.WeakNotifierCallback, Timer):
    """
    Weak variant of the Timer class.

    All references to the callback and supplied args/kwargs are weak
    references.  When any of the underlying objects are deleted,
    the WeakTimer is automatically stopped.
    """
    pass


class OneShotTimer(Timer):
    """
    A Timer that gets triggered exactly once when it is started.  Useful
    for deferred one-off tasks.

    Gotcha: it is possible to restart a OneShotTimer from inside the
    callback it invokes, however be careful not to return False in this
    case, otherwise the freshly started OneShotTimer will be implicitly
    stopped before it gets a chance to fire.
    """
    def __call__(self, *args, **kwargs):
        self.unregister()
        super(Timer, self).__call__(*args, **kwargs)
        return False


class WeakOneShotTimer(notifier.WeakNotifierCallback, OneShotTimer):
    """
    Weak variant of the OneshotTimer class.

    All references to the callback and supplied args/kwargs are weak
    references.  When any of the underlying objects are deleted,
    the WeakTimer is automatically stopped.
    """
    pass


class OneShotAtTimer(OneShotTimer):
    """
    A timer that is triggered at a specific time of day.  Once the timer fires
    it is stopped.
    """
    def start(self, hours=range(24), minutes=range(60), seconds=0, **kwargs):
        """
        Starts the timer, causing it to be fired at the specified time.

        By default, the timer will fire every minute at 0 seconds.  The timer
        has second precision.

        :param hours: the hour number (0-23) or list of hours
        :type hours: int or list of ints
        :param minutes: the minute number (0-59) or list of minutes
        :type minutes: int or list of ints
        :param seconds: the second number (0-59) or list of seconds
        :type seconds: int or list of ints
        """
        # Legacy support for hour, min, sec kwargs.
        hours = kwargs.get('hour', hours)
        minutes = kwargs.get('min', minutes)
        seconds = kwargs.get('sec', seconds)
        if not isinstance(hours, (list, tuple)):
            hours = [hours]
        if not isinstance(minutes, (list, tuple)):
            minutes = [minutes]
        if not isinstance(seconds, (list, tuple)):
            seconds = [seconds]

        self._timings = sorted(hours), sorted(minutes), sorted(seconds)
        self._last_time = datetime.datetime.now()
        self._schedule_next()


    def _schedule_next(self):
        """
        Internal function to calculate the next callback time and
        schedule it.
        """
        hour, min, sec = self._timings
        now = datetime.datetime.now()
        # Take the later of now or the last scheduled time for purposes of
        # determining the next time.  If we use the current system time
        # instead, we may end up firing a callback twice for a given time,
        # because due to imprecision we may end up here slightly before (a few
        # milliseconds) the scheduled time.
        t = max(self._last_time, now).replace(microsecond = 0)

        next_sec = [ x for x in sec if t.second < x ]
        next_min = [ x for x in min if t.minute < x ]
        next_hour = [ x for x in hour if t.hour < x ]

        if next_sec and t.minute in min and t.hour in hour:
            next = t.replace(second = next_sec[0])
        elif next_min and t.hour in hour:
            next = t.replace(minute = next_min[0], second = sec[0])
        elif next_hour:
            next = t.replace(hour = next_hour[0], minute = min[0], second = sec[0])
        else:
            tmrw = t + datetime.timedelta(days = 1)
            next = tmrw.replace(hour = hour[0], minute = min[0], second = sec[0])

        delta = next - now
        super(OneShotAtTimer, self).start(delta.seconds + delta.microseconds / 1000000.0)
        self._last_time = next


    @property
    def hours(self):
        """
        List of hours passed to :meth:`start`
        """
        return tuple(self._timings[0]) if getattr(self, '_timings', None) else ()

    @property
    def minutes(self):
        """
        List of minutes passed to :meth:`start`
        """
        return tuple(self._timings[1]) if getattr(self, '_timings', None) else ()

    @property
    def seconds(self):
        """
        List of seconds passed to :meth:`start`
        """
        return tuple(self._timings[2]) if getattr(self, '_timings', None) else ()


    @property
    def next(self):
        """
        A datetime object indicating the next time the timer will fire, or
        None if the time is not running.
        """
        # _last_time is the last time calculated, but actually the next time
        # the timer will fire.
        return self._last_time if getattr(self, '_last_time', None) else ()


class AtTimer(OneShotAtTimer):
    """
    A timer that is triggered at a specific time or times of day.
    """
    def __call__(self, *args, **kwargs):
        if super(Timer, self).__call__(*args, **kwargs) != False:
            self._schedule_next()
