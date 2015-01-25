# -* -coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# m2.py - M2Crypto backend for TLSSocket
# -----------------------------------------------------------------------------
# Copyright 2008-2012 Dirk Meyer, Jason Tackaberry
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

# python imports
import logging
import os
import M2Crypto
from M2Crypto import m2, X509

# kaa imports
import kaa
from .common import TLSError, TLSProtocolError, TLSVerificationError, TLSSocketBase

M2Crypto.threading.init()
kaa.signals['shutdown'].connect(M2Crypto.threading.cleanup)

# get logging object
log = logging.getLogger('kaa.base.net.tls.m2')


class _SSLWrapper:
    """
    Wrapper for an SSL object, which calls the low-level ssl_free() on the SSL
    object during destruction.  Also by pushing __del__ into here, it allows
    M2TLSSocket to be garbage collected.
    """

    m2_ssl_free = m2.ssl_free

    def __init__(self, ssl):
        self.obj = ssl

    def __del__(self):
        if self.obj is not None:
            self.m2_ssl_free(self.obj)


class _BIOWrapper:
    """
    Wrapper for a BIO object, which calls the low-level bio_free_all() on the
    BIO during destruction.  Also by pushing __del__ into here, it allows
    M2TLSSocket to be garbage collected.
    """

    m2_bio_free_all = m2.bio_free_all

    def __init__(self, bio, ssl):
        # Hold reference to SSL object to ensure _BIOWrapper.__del__ gets
        # called before _SSLWrapper.__del__.  Otherwise, if the SSL obj
        # gets freed before the BIO object, we will segfault.
        self.obj = bio
        self.ssl = ssl

    def __del__(self):
        if self.obj is not None:
            self.m2_bio_free_all(self.obj)


class M2TLSSocket(TLSSocketBase):
    """
    TLSSocket implementation that uses M2Crypto.  This class uses OpenSSL's BIO
    pairs for guaranteed async IO; all socket communication is handled by us
    (via the IOChannel).  See:

        http://www.openssl.org/docs/crypto/BIO_new_bio_pair.html

    Inspired heavily by TwistedProtocolWrapper.py from M2Crypto.
    """
    # list of suuported TLS authentication mechanisms
    supported_methods = [ 'X.509' ]

    def __init__(self):
        super(M2TLSSocket, self).__init__()
        self._reset()


    def _m2_check_err(self, r=None, cls=TLSError):
        if m2.err_peek_error():
            err = m2.err_reason_error_string(m2.err_get_error())
            raise cls(err)
        return r


    def _reset(self):
        self._buf_plaintext = []
        self._buf_ciphertext = []

        # Delete wrapper objects so the BIO/SSL objects get freed.
        self._bio_ssl = None
        self._bio_network = None
        self._ssl = None

        # True while performing initial handshake, False once it completes.
        self._handshake = False
        # True once starttls_*() has been called.
        self._tls_started = False
        # True once the peer's certificate has been verified (or ignored if verify=False)
        self._validated = False
        # True if starttls_client() was called, False otherwise.
        self._is_client = False
        # kwargs passed to starttls_(client|server) for use by _check()
        self._starttls_kwargs = None
        # InProgress finished when starttls completes or fails.
        self._tls_ip = kaa.InProgress()


    def close(self, immediate=False, expected=True):
        if not immediate and self._tls_started:
            # Send (or rather queue for write) an SSL shutdown message to the
            # client to gracefully terminate the session.
            m2.ssl_shutdown(self._ssl.obj)
            super(M2TLSSocket, self).write(self._encrypt())
        return super(M2TLSSocket, self).close(immediate, expected)


    def _close(self):
        super(M2TLSSocket, self)._close()
        self._reset()


    def _is_read_connected(self):
        """
        Returns True if we're interested in read events.
        """
        # While doing initial handshake from ClientHello, we are interested
        # in read events internally, even if we have no listeners.
        should_read = m2.bio_should_read(self._bio_ssl.obj) if self._bio_ssl else False
        return should_read or self._handshake or super(M2TLSSocket, self)._is_read_connected()


    # Useful for debug.
    #def _write(self, data):
    #    print 'm2: write len=%d data=%r...' % (len(data), data[:20])
    #    return super(M2TLSSocket, self)._write(data)


    def write(self, data):
        # A write can require us to read from the socket, even when there are
        # no callbacks attached to 'read' or 'readline', such as in the
        # case when a handshake is still pending.  If this is the case,
        # _encrypt() called below will cause _rmon to get registered while
        # the TLS layer needs data from the peer.
        if not self._tls_started:
            return super(M2TLSSocket, self).write(data)

        self._buf_plaintext.append(data)
        try:
            ip = super(M2TLSSocket, self).write(self._encrypt())
            # FIXME: this IP might not reflect the given data for this write()
            # if we're currently doing a handshake.
            return ip
        except M2Crypto.BIO.BIOError, e:
            raise TLSProtocolError(e.args[0])


    def _check(self):
        if self._validated or not m2.ssl_is_init_finished(self._ssl.obj):
            return

        kwargs = self._starttls_kwargs
        if kwargs.get('verify'):
            # See http://www.openssl.org/docs/apps/verify.html#DIAGNOSTICS
            # for the error codes returned by SSL_get_verify_result.
            if m2.ssl_get_verify_result(self._ssl.obj) != m2.X509_V_OK:
                raise TLSVerificationError('Peer certificate is not signed by a known CA')

        x509 = self._m2_check_err(m2.ssl_get_peer_cert(self._ssl.obj), TLSVerificationError)
        if x509 is not None:
            self.peer_cert = X509.X509(x509, 1)
        else:
            self.peer_cert = None

        if 'check' in kwargs or self.peer_cert:
            check = kwargs.get('check', (None, None))
            if check[0] is None:
                # Validate peer CN by default.
                host = self.peer[5]
            elif check[0] is False:
                # User requested to disable CN verification.
                host = None
            else:
                # User override for peer CN.
                host = check[0]
            fingerprint = check[1] if len(check) > 1 else None
            # TODO: normalize exceptions raised by Checker.
            M2Crypto.SSL.Checker.Checker(host, fingerprint)(self.peer_cert)

        self._validated = True


    def _read(self, chunk):
        data = super(M2TLSSocket, self)._read(chunk)
        if not self._tls_started or not data:
            if self._tls_started and not self._tls_ip.finished:
                e = TLSProtocolError('Peer terminated connection before TLS handshake completed')
                self._tls_ip.throw(TLSProtocolError, e, None)
            return data

        self._buf_ciphertext.append(data)
        decrypted = ''

        try:
            while True:
                plaintext = self._decrypt()
                self._check()
                ciphertext = self._encrypt()
                if ciphertext:
                    super(M2TLSSocket, self).write(ciphertext)

                if not plaintext and not ciphertext:
                    break
                decrypted += plaintext
        except M2Crypto.BIO.BIOError, e:
            e = TLSProtocolError(e.args[0])
            if not self._tls_ip.finished:
                self._tls_ip.throw(e.__class__, e, None)
            raise e

        if not self._tls_ip.finished and m2.ssl_is_init_finished(self._ssl.obj):
            # TLS handshake completed successfully, peer cert validated.
            self._handshake = False
            self._update_read_monitor()
            self._tls_ip.finish(True)

        if decrypted and not self._is_read_connected() and not self._is_readline_connected():
            # There is decrypted (user) data from the socket, but no one external is wants
            # it yet.  So this data was decrypted as a consequence of our handshaking.
            # (SSL BIO said we should read in _translate()).  We can stuff this data
            # into the read queue (from IOChannel superclass), so subsequent user reads
            # will consume it.
            if len(decrypted) + self.read_queue_used > self.queue_size + self.chunk_size:
                # This shouldn't happen in normal circumstances.  It's more of a sanity
                # check.
                raise TLSError('Read queue overflow')

            self._read_queue.write(decrypted)
            decrypted = None
            # We probably no longer need to read from the socket, given that we
            # have user data.
            self._update_read_monitor()

        if not decrypted:
            # We read data from the socket, but after passing through the BIO pair
            # there was no decrypted data.  So what we read was protocol traffic.
            # We signal to the underlying IOHandler that we want to continue
            # later by raising this.
            raise IOError(11, 'Resource temporarily unavailable')

        return decrypted


    def _hello(self):
        try:
            # We rely on OpenSSL implicitly starting with client hello
            # when we haven't yet established an SSL connection
            super(M2TLSSocket, self).write(self._encrypt(hello=True))
        except M2Crypto.BIO.BIOError, e:
            raise TLSProtocolError(e.args[0])


    def _starttls(self, **kwargs):
        self._is_client = kwargs['client']
        self._handshake = True
        self._update_read_monitor()

        ctx = kwargs.get('ctx', M2Crypto.SSL.Context())

        if 'dh' in kwargs:
            ctx.set_tmp_dh(kwargs['dh'])

        if 'cert' in kwargs:
            try:
                ctx.load_cert(kwargs['cert'], keyfile=kwargs.get('key'))
            except M2Crypto.SSL.SSLError, e:
                # Reraise wrapped as TLSSocketError
                raise TLSError('Invalid certificate and/or key: %s' % e.message)

        if kwargs.get('verify'):
            # TODO: apply appropriate verify options.
            #ctx.set_verify(M2Crypto.SSL.verify_none, 10)
            if not self._cafile:
                # Verification was requested but on CA bundle found, therefore
                # impossible to verify.
                raise TLSError('CA bundle not found but verification requested.')
            else:
                # Load CA bundle.
                ctx.load_verify_locations(self._cafile)
                # M2Crypto does no error checking on this function, and at
                # least on my system it yields the delightfully inscrutable
                # "cert already in hash table" error (perhaps my distro's
                # CA bundle has duplicate certs?).  It doesn't seem there's
                # anything that can be done about it, so just eat it.
                # (There may be multiple such errors, so clear them all.)
                while True:
                    err = m2.err_get_error()
                    if not err:
                        break
                    # The magic number is X509_R_CERT_ALREADY_IN_HASH_TABLE, which
                    # is a constant that m2crypto doesn't export. :/
                    if err != 185057381:
                        raise TLSError(m2.err_reason_error_string(err))


        # Create a lower level (SWIG) SSL object using this context.
        self._ssl = _SSLWrapper(m2.ssl_new(ctx.ctx))
        if kwargs['client']:
            self._m2_check_err(m2.ssl_set_connect_state(self._ssl.obj))
        else:
            self._m2_check_err(m2.ssl_set_accept_state(self._ssl.obj))

        # Setup the BIO pair.  This diagram is instructive:
        #
        #     Application         |   TLS layer
        #                         |
        #    Your Code            |
        #     /\    ||            |
        #     ||    \/            |
        #    Application buffer <===> TLS read/write/etc
        #                         |     /\    ||
        #                         |     ||    \/
        #                         |   BIO pair (internal_bio)
        #                         |   BIO pair (network_bio)
        #                         |     /\    ||
        #                         |     ||    \/
        #    socket read/write  <===> BIO read/write
        #     /\    ||            |
        #     ||    \/            |
        #     network             |
        #
        # [From http://www.mail-archive.com/openssl-users@openssl.org/msg57297.html]

        bio_internal = m2.bio_new(m2.bio_s_bio())
        bio_network = m2.bio_new(m2.bio_s_bio())
        self._m2_check_err(m2.bio_make_bio_pair(bio_internal, bio_network))
        self._bio_network = _BIOWrapper(bio_network, self._ssl)

        self._bio_ssl = _BIOWrapper(m2.bio_new(m2.bio_f_ssl()), self._ssl)
        self._m2_check_err(m2.ssl_set_bio(self._ssl.obj, bio_internal, bio_internal))
        self._m2_check_err(m2.bio_set_ssl(self._bio_ssl.obj, self._ssl.obj, m2.bio_noclose))

        # Need this for writes that are larger than BIO pair buffers
        mode = m2.ssl_get_mode(self._ssl.obj)
        mode |= m2.SSL_MODE_ENABLE_PARTIAL_WRITE | m2.SSL_MODE_ACCEPT_MOVING_WRITE_BUFFER
        self._m2_check_err(m2.ssl_set_mode(self._ssl.obj, mode))

        self._tls_started = True
        self._starttls_kwargs = kwargs
        if kwargs['client']:
            self._hello()
        return self._tls_ip


    def starttls_client(self, **kwargs):
        """
        TODO: document me.

        Possible kwargs:
            cert: filename to pem cert for local side
            key: private key file (if None, assumes key is in cert)
            dh: filename for Diffie-Hellman parameters (only used for server)
            verify: if True, checks that the peer cert is signed by a known CA
            check: 2-tuple (host, fingerprint) to control further peer cert checks:
                   host: None: validate CN from host from connect();
                         False: don't do any CN checking
                         string: require CN match the string
                   fingerprint: peer cert digest must match fingerprint, or None not to check.
        """
        return self._starttls(client=True, **kwargs)


    def starttls_server(self, **kwargs):
        return self._starttls(client=False, **kwargs)


    def _translate(self, write_bio, write_bio_buf, read_bio, force_write=False):
        data = []
        encrypting = write_bio is self._bio_ssl
        write_bio = write_bio.obj
        read_bio = read_bio.obj

        while True:
            writable = m2.bio_ctrl_get_write_guarantee(write_bio) > 0
            if (writable and write_bio_buf) or force_write:
                # If force_write is True, we want to start the handshake.  We call
                # bio_write() even if there's nothing in the buffer, to cause OpenSSL to
                # implicitly send the client hello.
                chunk = write_bio_buf.pop(0) if write_bio_buf else ''
                r = m2.bio_write(write_bio, chunk)
                if r <= 0:
                    # If BIO_write returns <= 0 due to an error condition, it should
                    # raise.  Otherwise we expect bio_should_retry() to return True.  Do a
                    # quick sanity check.
                    if not m2.bio_should_retry(write_bio):
                        raise TLSProtocolError('Unexpected internal state: should_retry()'
                                               'is False without error')

                    if not self._rmon.active and m2.bio_should_read(self._bio_ssl.obj):
                        # The BIO write failed, the SSL BIO is now telling us we should
                        # read, and the read monitor is not active.  Update the read
                        # monitor now, which will register with the notifier because the
                        # SSL BIO should read, allowing us to read from the socket to
                        # satisfy whatever the underlying SSL protocol is doing.
                        self._update_read_monitor()
                else:
                    if encrypting:
                        # We are encrypting user data to send to peer.  Require the
                        # remote end be validated first.  We should not normally
                        # get here until ClientHello is completed successfully.
                        assert(self._validated)
                    chunk = chunk[r:]

                if chunk:
                    # Insert remainder of chunk back into the buffer.
                    write_bio_buf.insert(0, chunk)

            pending = m2.bio_ctrl_pending(read_bio)
            if not pending:
                break

            chunk  = m2.bio_read(read_bio, pending)
            if chunk is not None:
                data.append(chunk)
            else:
                # It's possible for chunk to be None, even though bio_ctrl_pending()
                # told us there was data waiting in the BIO.  I suspect this happens
                # when all the bytes in the BIO are used for the SSL protocol and
                # none are user data.
                assert(m2.bio_should_retry(read_bio))

        return ''.join(data)


    def _encrypt(self, hello=False):
        #print 'ENCRYPT: buffers=', self._buf_plaintext
        return self._translate(self._bio_ssl, self._buf_plaintext, self._bio_network, hello)


    def _decrypt(self):
        #print 'DECRYPT: buffers=', self._buf_ciphertext
        return self._translate(self._bio_network, self._buf_ciphertext, self._bio_ssl)
