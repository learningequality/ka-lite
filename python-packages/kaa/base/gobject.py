# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# glib.py - Glib (gobject mainloop) thread wrapper
# -----------------------------------------------------------------------------
# This module makes it possible to run the glib mainloop in an extra thread
# and provides a hook to run callbacks in the glib thread. This module also
# supports using the glib mainloop as main mainloop. In that case, no threads
# are used.
#
# If you use this module to interact with a threaded glib mainloop, remember
# that callbacks from glib are also called from the glib thread.
#
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2008-2012 Dirk Meyer, Jason Tackaberry, et al.
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

__all__ = [ 'GOBJECT', 'gobject_set_threaded' ]

# python imports
import sys
import threading

from .weakref import weakref
try:
    if 'gi.repository' in sys.modules:
        # try to import gobject from gi.repository
        from gi.repository import GObject as gobject
    else:
        # try to import gobject
        import gobject
except ImportError:
    gobject = None

# get thread module
from . import thread as thread_support
from . import main as main_module

# object for kaa.threaded decorator
GOBJECT = object()

class Wrapper(object):
    """
    Glib wrapper with ThreadPool interface.
    """
    def __init__(self):
        self.stopped = False
        self.thread = False
        self.init = False
        # Fake pool members, needed by ThreadPool interface.
        self._members = [weakref(self)]


    def set_threaded(self, mainloop=None):
        """
        Start the gobject mainloop in a thread. This function should
        always be used together with the generic mainloop.  It is
        possible to jump between the gobject and the generic mainloop
        with the threaded decorator.

        :param mainloop: the mainloop object to use a mainloop based on gobject
          like the gstreamer or clutter mainloop. The object provided here must
          have a start and a stop function.
        """
        if self.init:
            raise RuntimeError('gobject loop already running')
        if self.thread:
            return
        self.thread = True

        # Register this class as a thread pool
        thread_support._thread_pools[GOBJECT] = self

        if gobject is not None:
            # init thread support in the module importing gobject
            gobject.threads_init()
            self.loop(mainloop)
            # make sure we get a clean shutdown
            main_module.signals['shutdown'].connect_once(self.stop, True)


    @thread_support.threaded()
    def loop(self, mainloop):
        """
        Glib thread.
        """
        self.thread = threading.currentThread()
        if mainloop is None:
            mainloop = gobject.MainLoop()
        self._loop = mainloop
        self._loop.run()


    def enqueue(self, callback, priority=0):
        """
        Add a callback.
        """
        self.init = True
        if not self.thread or threading.currentThread() == self.thread:
            return callback()
        if gobject is None:
            raise RuntimeError('gobject not available')
        gobject.idle_add(self._execute, callback)


    def _execute(self, callback):
        """
        Execute callback.
        """
        if callback is not None:
            callback()
        elif self.stopped:
            self._loop.quit()
        return False


    def stop(self, wait=False):
        """
        Stop the glib thread.
        """
        if not self.stopped:
            self.stopped = True
            if self.thread:
                self.enqueue(None)
        if wait:
            # wait until the thread is done
            self.join()


    def join(self):
        """
        Wait until the thread is done.
        """
        if self.thread:
            # join the thread
            self.thread.join()


# create object and expose set_threaded
gobject_set_threaded = Wrapper().set_threaded
