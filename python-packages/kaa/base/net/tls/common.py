# -* -coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# tls.py - TLS support for the Kaa Framework based on tlslite
# -----------------------------------------------------------------------------
# This module wraps TLS for client and server based on tlslite. See
# http://trevp.net/tlslite/docs/public/tlslite.TLSConnection.TLSConnection-class.html
# for more information about optional paramater.
#
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

# python imports
import logging
import os

# kaa imports
import kaa

# get logging object
log = logging.getLogger('kaa.base.net.tls')

# Search these standard system locations for the CA bundle.
CA_SEARCH_PATH = (
    '/etc/pki/tls/certs/ca-bundle.crt',
    '/usr/share/ssl/certs/ca-bundle.crt',
    '/usr/local/share/ssl/certs/ca-bundle.crt',
    '/etc/ssl/certs/ca-certificates.crt'
)

class TLSError(Exception):
    """
    Base class for all TLS/SSL exceptions.

    Exception args is a message string.
    """
    pass

class TLSProtocolError(TLSError):
    """
    Raised when a protocol-related problem occurs, such as the remote end does
    not speak TLS, or when no shared cipher could be established.
    """
    pass

class TLSVerificationError(TLSError):
    """
    Raised when the remote end's certificate did not verify correctly.
    """
    pass



class TLSSocketBase(kaa.Socket):
    # list of suuported TLS authentication mechanisms (subclass must override)
    supported_methods = []
    
    # Cached system-wide CA cert file (as detected), or None if none was found.
    _cafile = False

    __kaasignals__ = {
        'tls':
            '''
            Emitted when a TLS handshake has been successfully completed.
            '''
    }

    def __init__(self, cafile=None):
        super(TLSSocketBase, self).__init__()
        self._handshake = False
        self._pre_handshake_write_queue = []

        if cafile:
            self._cafile = cafile
        elif TLSSocketBase._cafile is False:
            self._cafile = None
            for path in CA_SEARCH_PATH:
                if os.path.exists(path):
                    cafile = path
                    break
            else:
                # Maybe locate(1) can help.
                # XXX: assumes this is fast.  Maybe this should be done async.
                path = os.popen('locate -l 1 ca-certificates.crt ca-bundle.crt 2>/dev/null').readline().strip()
                if os.path.exists(path):
                    cafile = path

            TLSSocketBase._cafile = self._cafile = cafile


# FIXME: we need a TLSKey abstraction.
