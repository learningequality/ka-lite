# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# event.py - Generic event handling
#
# Events are similar to Signals but use a different approach. They are
# global and always synchronized. An EventHandler can monitor specific
# or all events; it does not even need to know which events
# exist. Events are always send to the EventHandlers synchronized.
# This means that a second event is delayed until the first event is
# handled by all handlers. If a handler posts another event it is
# delayed; the ordering also respects InProgress results and waits
# until it is finished before processing the next event.
#
# Events are designed for the application using kaa and make only
# sense in its context. No kaa library is posting an event.
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2005-2013 Dirk Meyer, Jason Tackaberry, et al.
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

__all__ = [ 'Event', 'EventHandler', 'WeakEventHandler' ]

# python imports
import copy
import logging

# kaa.base imports
from .callable import Callable, WeakCallable
from .core import CoreThreading
from .thread import MainThreadCallable
from .main import signals
from .coroutine import coroutine, POLICY_SYNCHRONIZED
from .async import InProgress

# get logging object
log = logging.getLogger('kaa.base.core')

# manager object for eveny handling
manager = None

class Event(object):
    """
    A simple event that can be passed to the registered event handler.
    """
    def __init__(self, name, *arg):
        """
        Init the event.
        """
        if isinstance(name, Event):
            self.name = name.name
            self._arg  = name._arg
        else:
            self.name = name
            self._arg  = None
        if arg:
            self.arg = arg

    @property
    def arg(self):
        """
        Get event arguments
        """
        return self._arg

    @arg.setter
    def arg(self, arg):
        """
        Set event arguments
        """
        if not arg:
            self._arg = None
        elif hasattr(arg, '__len__') and len(arg) == 1:
            self._arg = arg[0]
        else:
            self._arg = arg

    def post(self, *arg):
        """
        Post event
        """
        event = self
        if arg:
            event = copy.copy(self)
            event.arg = arg
        if not CoreThreading.is_mainthread():
            return MainThreadCallable(manager.post, event)()
        else:
            return manager.post(event)

    def __str__(self):
        """
        Return the event as string
        """
        return self.name

    def __cmp__(self, other):
        """
        Compare function, return 0 if the objects are identical, 1 otherwise
        """
        if not other:
            return 1
        if isinstance(other, Event):
            return self.name != other.name
        return self.name != other

    def __eq__(self, other):
        """
        Compare function, return 0 if the objects are identical, 1 otherwise
        """
        if isinstance(other, Event):
            return self.name == other.name
        return self.name == other


class EventHandler(Callable):
    """
    Event handling callback.
    """
    def register(self, events=[]):
        """
        Register to a list of events. If no event is given, all events
        will be used.
        """
        self.events = events
        if not self in manager.handler:
            manager.handler.append(self)

    @property
    def active(self):
        """
        True if the object is bound to the event manager.
        """
        return self in manager.handler

    def unregister(self):
        """
        Unregister callback.
        """
        if self in manager.handler:
            manager.handler.remove(self)

    def __call__(self, event):
        """
        Invoke wrapped callable if the event matches.
        """
        if not self.events or event in self.events:
            return super(EventHandler, self).__call__(event)


class WeakEventHandler(WeakCallable, EventHandler):
    """
    Weak reference version of the EventHandler.
    """
    pass


class EventManager(object):
    """
    Class to manage Event and EventHandler objects.
    Internal use only.
    """
    def __init__(self):
        self.active = False
        self.handler = []

    def post(self, event):
        """
        Post event
        """
        signals['step'].connect_once(self.handle, event)

    @coroutine(policy=POLICY_SYNCHRONIZED)
    def handle(self, event):
        """
        Handle the next event.
        """
        try:
            for handler in self.handler[:]:
                result = handler(event)
                if isinstance(result, InProgress):
                    yield result
        except Exception, e:
            log.exception('event callback')

manager = EventManager()
