# -* -coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# gnutls.py - Gnutls backend for TLSSocket
# -----------------------------------------------------------------------------
# Gnutls seems to be the most promising TLS library we could use. It
# supports everything from certificates over OpenGPG to SRP. This lib
# uses python-gnutls from http://pypi.python.org/pypi/python-gnutls.
#
# FIXME: The main problem is the lack of SRP support in all python
# wrappers. I tried to add it, but I failed on server side. I may not
# have a key file and therefore need a callback function. But I have
# no idea how to do this using ctypes due to the complexity of the
# callback. On the other hand, maybe it is easier to define a simple C
# module doing the hard part.
#
# -----------------------------------------------------------------------------
# Copyright 2010-2012 Dirk Meyer
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

import sys
import os
import socket
import logging
import kaa

from .common import TLSSocketBase

import gnutls.connection
from gnutls.connection import X509Certificate, X509PrivateKey, X509Certificate, X509CRL, X509Credentials

# get logging object
log = logging.getLogger('kaa.base.net.tls.gnutls')

# Search these standard system locations for the CA bundle.
CA_SEARCH_PATH = (
    '/etc/pki/tls/certs/ca-bundle.crt',
    '/usr/share/ssl/certs/ca-bundle.crt',
    '/usr/local/share/ssl/certs/ca-bundle.crt',
    '/etc/ssl/certs/ca-certificates.crt'
)


# import ctypes
# 
# c_gnutls = gnutls.library.functions._libraries['libgnutls.so.26']
# 
# class gnutls_srp_credentials_st(ctypes.Structure):
#     pass
# gnutls_srp_credentials_st._fields_ = []
# gnutls_srp_credentials_t = ctypes.POINTER(gnutls_srp_credentials_st)
# 
# gnutls_srp_allocate_client_credentials = c_gnutls.gnutls_srp_allocate_client_credentials
# gnutls_srp_allocate_client_credentials.restype = ctypes.c_int
# gnutls_srp_allocate_client_credentials.argtypes = [ctypes.POINTER(gnutls_srp_credentials_t)]
# gnutls_srp_set_client_credentials = c_gnutls.gnutls_srp_set_client_credentials
# gnutls_srp_set_client_credentials.restype = ctypes.c_int
# gnutls_srp_set_client_credentials.argtypes = [gnutls_srp_credentials_t]
# gnutls_srp_free_client_credentials = c_gnutls.gnutls_srp_free_client_credentials
# gnutls_srp_free_client_credentials.restype = None
# gnutls_srp_free_client_credentials.argtypes = [gnutls_srp_credentials_t]
# 
# class SRPCredentials(object):
# 
#     def __new__(cls, *args, **kwargs):
#         c_object = gnutls_srp_credentials_t()
#         gnutls_srp_allocate_client_credentials(ctypes.byref(c_object))
#         instance = object.__new__(cls)
#         instance._c_object = c_object
#         return instance
# 
#     def __init__(self, username, password):
#         self._type = ctypes.c_int(3)
#         self.username = username
#         self.password = password
#         gnutls_srp_set_client_credentials(self._c_object, username, password);
#     
#     def __del__(self):
#         gnutls_srp_free_client_credentials(self._c_object)


class GNUTLSSocket(TLSSocketBase):

    def _is_read_connected(self):
        """
        Returns True if we're interested in read events.
        """
        # During the handshake stage, we handle all reads internally (within
        # TLSConnection).  So if self._handshake is True, we return False here
        # to prevent the IOChannel from responding to reads and passing data
        # from the TLS handshake back to the user.  If it's False, we defer to
        # the default behaviour.
        return not self._handshake and super(GNUTLSSocket, self)._is_read_connected()


    def _handle_write(self):
        if self._handshake:
            # Before starting the TLS handshake we created a new write
            # queue. The data send before TLS was started
            # (_pre_handshake_write_queue) must be send, after that we
            # give control over the socket to the TLS layer. Data
            # written while doing the handshake is send after it.
            if not self._pre_handshake_write_queue:
                # No data to send before the handshake
                return
            try:
                # Switch queues and send pre handshake data
                queue = self._write_queue
                self._write_queue = self._pre_handshake_write_queue
                super(GNUTLSSocket, self)._handle_write()
            finally:
                self._write_queue = queue
        else:
            # normal operation
            super(GNUTLSSocket, self)._handle_write()
            
    @kaa.coroutine()
    def _handle_handshake(self, session):
        self._handshake = True
        # Store current write queue and create a new one
        self._pre_handshake_write_queue = self._write_queue
        self._write_queue = []
        if self._pre_handshake_write_queue:
            # flush pre handshake write data
            yield self._pre_handshake_write_queue[-1][1]
        self._rmon.unregister()
        while True:
            try:
                session.handshake()
                break
            except gnutls.connection.OperationWouldBlock, e:
                cb = kaa.InProgressCallable()
                disp = kaa.IOMonitor(cb)
                disp.register(self.fileno, kaa.IO_READ)
                yield cb
                disp.unregister()
        self._channel = session
        self._update_read_monitor()
        self._handshake = False
        
    @kaa.coroutine()
    def handshake_client(self, credentials, srp=None):
        session = gnutls.connection.ClientSession(self._channel, credentials)
        # if srp:
        #     c_gnutls.gnutls_priority_set_direct(session._c_object, "NORMAL:+SRP:+SRP-RSA:+SRP-DSS", None);
        #     c_gnutls.gnutls_credentials_set(session._c_object, srp._type, ctypes.cast(srp._c_object, ctypes.c_void_p))
        yield self._handle_handshake(session)

    @kaa.coroutine()
    def handshake_server(self, credentials, srp=None):
        session = gnutls.connection.ServerSession(self._channel, credentials)
        # if srp:
        #     c_gnutls.gnutls_priority_set_direct(session._c_object, "NORMAL:+SRP:+SRP-RSA:+SRP-DSS", None);
        #     c_gnutls.gnutls_credentials_set(session._c_object, srp._type, ctypes.cast(srp._c_object, ctypes.c_void_p))
        yield self._handle_handshake(session)

    def _close(self):
        self._channel.bye()
        self._channel.shutdown()
        super(GNUTLSSocket, self)._close()

    @property
    def peer_certificate(self):
        if isinstance(self._channel, gnutls.connection.Session):
            return self._channel.peer_certificate
        return None
