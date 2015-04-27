# -* -coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# tlslite.py - tlslite backend for TLSSocket
# -----------------------------------------------------------------------------
# This module wraps TLS for client and server based on tlslite. See
# http://trevp.net/tlslite/docs/public/tlslite.TLSConnection.TLSConnection-class.html
# for more information about optional paramater.
#
# -----------------------------------------------------------------------------
# Copyright 2008-2012 Dirk Meyer
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

# python imports
from __future__ import absolute_import
import logging
import os
try:
    import tlslite.api as tlsapi
    from tlslite.errors import TLSAuthenticationError
except ImportError:
    import gdata.tlslite.api as tlsapi
    from gdata.tlslite.errors import TLSAuthenticationError

# kaa imports
import kaa
from .common import TLSError, TLSProtocolError, TLSVerificationError, TLSSocketBase

# get logging object
log = logging.getLogger('kaa.base.net.tls.tlslite')


class TLSKey(object):
    """
    Class to hold the public (and private) key together with the certification chain.
    This class can be used with TLSSocket as key.
    """
    def __init__(self, filename, private, *certs):
        self.private = tlsapi.parsePEMKey(open(filename).read(), private=private)
        self.certificate = tlsapi.X509()
        self.certificate.parse(open(filename).read())
        chain = []
        for cert in (filename, ) + certs:
            x509 = tlsapi.X509()
            x509.parse(open(cert).read())
            chain.append(x509)
        self.certificate.chain = tlsapi.X509CertChain(chain)


class TLSLiteConnection(tlsapi.TLSConnection):
    """
    This class wraps a socket and provides TLS handshaking and data transfer.
    It enhances the tlslite version of the class with the same name with
    kaa support.
    """
    @kaa.coroutine()
    def _iterate_handshake(self, handshake):
        """
        Iterate through the TLS handshake for asynchronous calls using
        kaa.IOMonitor and kaa.InProgressCallback.
        """
        try:
            while True:
                n = handshake.next()
                cb = kaa.InProgressCallable()
                disp = kaa.IOMonitor(cb)
                if n == 0:
                    disp.register(self.sock.fileno(), kaa.IO_READ)
                if n == 1:
                    disp.register(self.sock.fileno(), kaa.IO_WRITE)
                yield cb
                disp.unregister()
        except StopIteration:
            pass

    def handshakeClientCert(self, certChain=None, privateKey=None, session=None,
                            settings=None, checker=None):
        """
        Perform a certificate-based handshake in the role of client.
        """
        handshake = tlsapi.TLSConnection.handshakeClientCert(
            self, certChain=certChain, privateKey=privateKey, session=session,
            settings=settings, checker=checker, async=True)
        return self._iterate_handshake(handshake)

    def handshakeClientSRP(self, username, password, session=None,
                           settings=None, checker=None):
        """
        Perform a SRP-based handshake in the role of client.
        """
        handshake = tlsapi.TLSConnection.handshakeClientSRP(
            self, username=username, password=password, session=session,
            settings=settings, checker=checker, async=True)
        return self._iterate_handshake(handshake)

    def handshakeServer(self, sharedKeyDB=None, verifierDB=None, certChain=None,
                        privateKey=None, reqCert=None, sessionCache=None,
                        settings=None, checker=None):
        """
        Start a server handshake operation on the TLS connection.
        """
        handshake = tlsapi.TLSConnection.handshakeServerAsync(
            self, sharedKeyDB, verifierDB, certChain, privateKey, reqCert,
            sessionCache, settings, checker)
        return self._iterate_handshake(handshake)


    def fileno(self):
        """
        Return socket descriptor. This makes this class feel like a normal
        socket to the IOMonitor.
        """
        return self.sock.fileno()


    def close(self):
        """
        Close the socket.
        """
        if not self.closed:
            # force socket close or this will block
            # on kaa shutdown.
            self.sock.close()
        return tlsapi.TLSConnection.close(self)



class TLSLiteSocket(TLSSocketBase):
    # list of suuported TLS authentication mechanisms
    supported_methods = [ 'X.509', 'SRP' ]

    def _is_read_connected(self):
        """
        Returns True if we're interested in read events.
        """
        # During the handshake stage, we handle all reads internally (within
        # TLSConnection).  So if self._handshake is True, we return False here
        # to prevent the IOChannel from responding to reads and passing data
        # from the TLS handshake back to the user.  If it's False, we defer to
        # the default behaviour.
        return not self._handshake and super(TLSSocketBase, self)._is_read_connected()


    @kaa.coroutine()
    def _prepare_tls(self):
        """
        Prepare TLS handshake. Flush the data currently in the write buffer
        and return the TLS connection object
        """
        self._handshake = True
        # Store current write queue and create a new one
        self._pre_handshake_write_queue = self._write_queue
        self._write_queue = []
        if self._pre_handshake_write_queue:
            # flush pre handshake write data
            yield self._pre_handshake_write_queue[-1][1]

        self._rmon.unregister()


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
                super(TLSSocketBase, self)._handle_write()
            finally:
                self._write_queue = queue
        else:
            # normal operation
            super(TLSSocketBase, self)._handle_write()


    @kaa.coroutine()
    def _starttls(self, mode, *args, **kwargs):
         # TODO: accept 'verify' and 'check' kwargs like the m2 backend
        if not self.connected:
            raise TLSError('Socket not connected')

        self._handshake = True
        try:
            yield self._prepare_tls()
            yield getattr(self, '_tls_' + mode)(*args, **kwargs)
            self.signals['tls'].emit()
        finally:
            self._update_read_monitor()
            self._handshake = False

    def starttls_client(self, *args, **kwargs):
        return self._starttls('client', *args, **kwargs)
        
    def starttls_server(self, *args, **kwargs):
        return self._starttls('server', *args, **kwargs)



    @kaa.coroutine()
    def _tls_client(self, session=None, key=None, srp=None, checker=None):
        """
        Start a certificate-based handshake in the role of a TLS client.
        Note: this function DOES NOT check the server key based on the
        key chain. Provide a checker callback to be called for verification.
        http://trevp.net/tlslite/docs/public/tlslite.Checker.Checker-class.html
        Every callable object can be used as checker.

        @param session: tlslite.Session object to resume
        @param key: TLSKey object for client authentication
        @param srp: username, password pair for SRP authentication
        @param checker: callback to check the credentials from the server
        """
        if not self._rmon:
            raise TLSError('Socket not connected')

        if session is None:
            session = tlsapi.Session()

        # create TLS connection object and unregister the read monitor
        tlscon = TLSLiteConnection(self._channel)
        tlscon.ignoreAbruptClose = True
        if key:
            yield tlscon.handshakeClientCert(session=session, checker=checker,
                      privateKey=key.private, certChain=key.certificate.chain)
        elif srp:
            yield tlscon.handshakeClientSRP(session=session, checker=checker,
                      username=srp[0], password=srp[1])
        else:
            yield tlscon.handshakeClientCert(session=session, checker=checker)
        self._channel = tlscon


    @kaa.coroutine()
    def _tls_server(self, session=None, key=None, request_cert=False, srp=None, checker=None):
        """
        Start a certificate-based or SRP-based handshake in the role of a TLS server.
        Note: this function DOES NOT check the client key if requested,
        provide a checker callback to be called for verification.
        http://trevp.net/tlslite/docs/public/tlslite.Checker.Checker-class.html
        Every callable object can be used as checker.

        @param session: tlslite.Session object to resume
        @param key: TLSKey object for server authentication
        @param request_cert: Request client certificate
        @param srp: tlslite.VerifierDB for SRP authentication
        @param checker: callback to check the credentials from the server
        """
        # create TLS connection object and unregister the read monitor
        tlscon = TLSLiteConnection(self._channel)
        tlscon.ignoreAbruptClose = True
        kwargs = {}
        if key:
            kwargs['privateKey'] = key.private
            kwargs['certChain'] = key.certificate.chain
        if srp:
            kwargs['verifierDB'] = srp
        if request_cert:
            kwargs['reqCert'] = True
        yield tlscon.handshakeServer(checker=checker, **kwargs)
        self._channel = tlscon
