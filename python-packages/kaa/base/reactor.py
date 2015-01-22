# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# reactor.py - Twisted integration code
# -----------------------------------------------------------------------------
# Twisted reactor to run the kaa mainloop as twisted reactor.
#
# import kaa.reactor
# kaa.reactor.install()
#
# You can start/stop the loop with (reactor|kaa.main).(start|stop)
#
# -----------------------------------------------------------------------------
# kaa.base - The Kaa Application Framework
# Copyright 2007-2012 Dirk Meyer, Jason Tackaberry, et al.
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

__all__ = [ 'install' ]

# Twisted imports
import twisted

if twisted.version.major < 8:
    raise ImportError('Twisted >= 0.8.0 required')

from twisted.internet import _threadedselect as threadedselectreactor

# kaa imports
from .thread import MainThreadCallable
from .core import CoreThreading
from . import main

class KaaReactor(threadedselectreactor.ThreadedSelectReactor):
    """
    Twisted reactor for kaa
    """

    _twisted_stopped = False

    def _kaa_callback(self, func):
        """
        Callback from the Twisted thread kaa should execute from
        the mainloop.
        """
        MainThreadCallable(func)()

    def _twisted_stopped_callback(self):
        """
        Callback when Twisted wants to stop.
        """
        if not CoreThreading.is_mainthread():
            return MainThreadCallable(self._twisted_stopped_callback)()
        self._twisted_stopped = True
        # shut down kaa mainloop in case the reactor was shut down and
        # not kaa.main
        main.stop()

    def _twisted_stop(self):
        """
        Stop Twisted reactor and wait until it is done
        """
        if self._twisted_stopped:
            return
        self.stop()
        while not self._twisted_stopped:
            main.step()

    def connect(self):
        """
        Connect the reactor to kaa.
        """
        self.interleave(self._kaa_callback)
        self.addSystemEventTrigger('after', 'shutdown', self._twisted_stopped_callback)
        main.signals['shutdown'].connect(self._twisted_stop)

    def run(self, installSignalHandlers=1):
        """
        Run the reactor by starting the generic mainloop.
        """
        main.run()


def install():
    """
    Configure the twisted mainloop to be run using the kaa reactor.
    """
    reactor = KaaReactor()
    from twisted.internet.main import installReactor
    installReactor(reactor)
    reactor.connect()
    return reactor
