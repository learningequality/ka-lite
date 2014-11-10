# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# sockets.py - TCP/Unix Socket for the Kaa Framework
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

__all__ = [ 'Socket', 'SocketError' ]

import sys
import errno
import os
import re
import socket
import logging
import ctypes.util
import collections

from .errors import SocketError
from .utils import property, tempfile
from .thread import threaded
from .async import InProgress
from .io import IO_READ, IO_WRITE, IOChannel, WeakIOMonitor

# get logging object
log = logging.getLogger('kaa.base.sockets')


TIMEOUT_SENTINEL = getattr(socket, '_GLOBAL_DEFAULT_TIMEOUT', object())


# Implement functions for converting between interface names and indexes.
# Unfortunately these functions are not provided by the standard Python
# socket library, so we must implement them ourselves with ctypes.

def _libc():
    """
    On-demand loading of libc.  Don't do this at initial import as the overhead
    is non-trivial.
    """
    try:
        return _libc._lib
    except AttributeError:
        pass

    _libc._lib = None
    if ctypes.util.find_library('c'):
        # ctypes in python >= 2.6 supports errno.
        kwargs = {'use_errno': True} if sys.hexversion >= 0x02060000 else {}
        _libc._lib = ctypes.CDLL(ctypes.util.find_library('c'), **kwargs)
    return _libc._lib


def if_nametoindex(name):
    """
    Returns the interface index number for the given interface name.

    :param name: name of the interface
    :type name: str
    :returns: integer of the interface id
    :raises: ValueError if the interface name cannot be found;
             NotImplementedError on unsupported platforms.
    """
    try:
        idx = _libc().if_nametoindex(name)
    except AttributeError:
        raise NotImplementedError('Platform does not support if_nametoindex()')

    if idx <= 0:
        raise ValueError('Interface "%s" not found' % name)
    return idx


def if_indextoname(idx):
    """
    Returns the interface name for the given interface index number.

    :param idx: the index for the interface
    :type idx: int
    :returns: name of the index
    :raises: ValueError if the interface index is not found;
             NotImplementedError on unsupported platforms.
    """
    # Array must be at least IF_NAMESIZE, which is 16.  Double it for good measure.
    name = ctypes.create_string_buffer(32)
    try:
        ret = _libc().if_indextoname(idx, name)
    except AttributeError:
        raise NotImplementedError('Platform does not support if_indextoname()')

    if not ret:
        err = 'Failed to lookup interface index %d' % idx
        if hasattr(ctypes, 'get_errno'):
            err += ': ' + os.strerror(ctypes.get_errno())
        raise ValueError(err)

    return name.value



class Socket(IOChannel):
    """
    Communicate over TCP or Unix sockets, implementing fully asynchronous reads
    and writes.

    kaa.Socket requires an IPv6-capable stack, and favors IPv6 connectivity
    when available.  This should generally be completely transparent on
    IPv4-only networks.  See :meth:`~kaa.Socket.connect` for more information.
    """
    __kaasignals__ = {
        'new-client-connecting':
            '''
            Emitted when a new client is attempting to connect to a listening
            socket, but before the connection is accepted.

            ``def callback(...)``

            If :attr:`~kaa.Socket.auto_accept` is True (default), this signal
            can be used to prevent the client connection by returning False from
            the callback. If False, the callback must explicitly call
            :meth:`~kaa.Socket.listen` or the client will not be connected.
            ''',

        'new-client':
            '''
            Emitted when a new client connects to a listening socket.

            ``def callback(client, ...)``

            :param client: the new client that just connected.
            :type client: :class:`~kaa.Socket` object
            '''
    }

    @staticmethod
    def normalize_address(addr):
        """
        Converts supported address formats into a normalized 4-tuple (hostname,
        port, flowinfo, scope).  See connect() and listen() for supported
        formats.

        Service names are resolved to port numbers, and interface names are
        resolved to scope ids.  However, hostnames are not resolved to IPs
        since that can block.  Unspecified port or interface name will produced
        0 values for those fields.

        A non-absolute unix socket name will converted to a full path using
        kaa.tempfile().

        If we can't make sense of the given address, a ValueError exception will
        be raised.
        """
        if isinstance(addr, int):
            # Only port number specified; translate to tuple that can be
            # used with socket.bind()
            return ('', addr, 0, 0)
        elif isinstance(addr, basestring):
            m = re.match(r'^(\d+\.\d+\.\d+\.\d+)(?::(\d+))?', addr)
            if m:
                # It's an IPv4 address.
                return (m.group(1), int(m.group(2) or 0), 0, 0)
            elif ':' not in addr:
                # Treat as unix socket.
                return tempfile(addr) if not addr.startswith('/') else addr

            # See if it's an IPv6 address
            m = re.match(r'^ (\[(?:[\da-fA-F:]+)\] | (?:[^:]+) )? (?::(\w+))? (?:%(\w+))? ', addr, re.X)
            if not m:
                raise ValueError('Invalid format for address')
            addr = m.group(1) or '', m.group(2) or 0, 0, m.group(3) or 0
            if addr[0].isdigit():
                # Sanity check: happens when given ipv6 address without []
                raise ValueError('Invalid hostname: perhaps ipv6 address is not wrapped in []?')

        elif not isinstance(addr, (tuple, list)) or len(addr) not in (2, 4):
            raise ValueError('Invalid address specification (must be str, or 2- or 4-tuple)')

        if len(addr) == 2:
            # Coerce to 4-tuple, assume 0 for both scope and flowid.
            addr = addr + (0, 0)

        host, service, flowinfo, scopeid = addr
        # Strip [] from ipv6 addr
        if host.startswith('[') and host.endswith(']'):
            host = host[1:-1]
        # Resolve service name to port number
        if isinstance(service, basestring):
            service = int(service) if service.isdigit() else socket.getservbyname(service)
        # Resolve interface names to index values
        if isinstance(scopeid, basestring):
            scopeid = int(scopeid) if scopeid.isdigit() else if_nametoindex(scopeid)

        return host, service, flowinfo, scopeid



    @staticmethod
    def create_connection(addr=None, timeout=TIMEOUT_SENTINEL, source_address=None,
                          overwrite=False, ipv6=True):
        addr = Socket.normalize_address(addr) if addr else None
        source_address = Socket.normalize_address(source_address) if source_address else None

        if isinstance(addr, str) or isinstance(source_address, str):
            sockaddr = addr or source_address
            if overwrite and os.path.exists(sockaddr):
                # Unix socket exists; test to see if it's active.
                try:
                    dummy = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    dummy.connect(sockaddr)
                except socket.error, (err, msg):
                    if err == errno.ECONNREFUSED:
                        # Socket is not active, so we can remove it.
                        log.debug('Replacing dead unix socket at %s' % sockaddr)
                    else:
                        # Reraise unexpected exception
                        raise
                else:
                    # We were able to connect to the existing socket, so it's
                    # in use.  We won't overwrite it.
                    raise IOError(errno.EADDRINUSE, 'Address already in use')
                os.unlink(sockaddr)

            sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            if addr:
                sock.connect(addr)
            else:
                sock.bind(source_address)
            return sock


        # Not a unix socket ...
        req_family = socket.AF_UNSPEC if ipv6 else socket.AF_INET
        addr_addrinfo = source_addrinfo = None
        if source_address:
            # If link-local address is specified, make sure the scopeid is given.
            if source_address[0].lower().startswith('fe80::'):
                if not source_address[3]:
                    raise ValueError('Binding to a link-local address requires scopeid')
            elif not source_address[0]:
                source_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 0, 0, source_address)]
            elif source_address[0] == '::' and ipv6:
                source_addrinfo = [(socket.AF_INET6, socket.SOCK_STREAM, 0, 0, source_address)]
            else:
                source_addrinfo = socket.getaddrinfo(source_address[0], source_address[1],
                                                     req_family, socket.SOCK_STREAM)
                if not source_addrinfo:
                    raise socket.error('getaddrinfo returned empty list for source address')

        if addr:
            addr_addrinfo = socket.getaddrinfo(addr[0], addr[1], req_family, socket.SOCK_STREAM)
            if not addr_addrinfo:
                raise socket.error('getaddrinfo returned empty list for destination address')

        # At least on Linux, returned list is ordered to prefer IPv6 addresses
        # provided that a route is available to them.  We try all addresses
        # until we get a connection, and if all addresses fail, then we raise
        # the _first_ exception.
        err = sock = None

        for res in (source_addrinfo or [(None,) * 5]):
            b_af, b_socktype, b_proto, b_cn, b_sa = res
            if b_af is not None:
                try:
                    sock = socket.socket(b_af, b_socktype, b_proto)
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    b_sa = b_sa[:2] + source_address[2:]
                    sock.bind(b_sa if b_af == socket.AF_INET6 else b_sa[:2])
                except socket.error:
                    err = sys.exc_info() if not err else err
                    sock = None
                    continue

            if not addr_addrinfo and sock:
                # Nothing to connect to and we bound successfully, so done.
                return sock

            for (af, socktype, proto, cn, sa) in addr_addrinfo:
                if b_af is not None and af != b_af:
                    # Different address family than socket was bound to.
                    continue

                try:
                    if not sock:
                        sock = socket.socket(af, socktype, proto)
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    if timeout is not TIMEOUT_SENTINEL:
                        sock.settimeout(timeout)
                    sock.connect(sa)
                    return sock
                except socket.error:
                    err = sys.exc_info() if not err else err
                    sock = None
        else:
            if err:
                raise err[0], err[1], err[2]
            else:
                raise socket.error('destination had no addresses in source address family')



    def __init__(self, buffer_size=None, chunk_size=1024*1024):
        self._connecting = False
        self._listening = False
        self._buffer_size = buffer_size
        # Requested hostname passed to connect()
        self._reqhost = None
        self._auto_accept = True
        # If an InProgress object then there is an accept() call in progress,
        # otherwise None.
        self._accept_inprogress = None

        super(Socket, self).__init__(chunk_size=chunk_size)


    def _make_new(self):
        return self.__class__()


    @IOChannel.fileno.getter
    def fileno(self):
        # If fileno() is accessed on a closed socket, socket.error is
        # railsed.  So we override our superclass's implementation to
        # handle this case.
        try:
            return self._channel.fileno()
        except (AttributeError, socket.error):
            return None

    @property
    def auto_accept(self):
        """
        If True (default), automatically accept new clients connecting to
        listening sockets.

        See :meth:`listen` for more details.
        """
        return self._auto_accept


    @auto_accept.setter
    def auto_accept(self, value):
        self._auto_accept = value


    @property
    def address(self):
        """
        This property is deprecated; use *peer* instead.
        """
        log.warning('Socket.address is deprecated; use Socket.peer instead')
        return self.local[:2]


    @property
    def local(self):
        """
        Information about the local side of the socket.

        This is either the tuple ``(host, port, flowinfo, scopeid, scope)``
        representing the local end of a TCP socket, or the string containing
        the name of a Unix socket.

        *scope* is the interface name represented by *scopeid*, and is None if
        *scopeid* is 0.

        On Python 2.6 and later, the returned value is a namedtuple.
        """
        return self._make_address_tuple(self._channel.getsockname())


    @property
    def peer(self):
        """
        Information about the remote side of the socket.

        This is a tuple ``(host, port, flowinfo, scopeid, scope, reqhost)``
        representing the remote end of the socket.

        *scope* is the interface name represented by *scopeid*, and is None if
        *scopeid* is 0.  *reqhost* is the requested hostname if
        :meth:`~kaa.Socket.connect` was called, or None if this is a listening
        socket.

        On Python 2.6 and later, the returned value is a namedtuple.
        """
        return self._make_address_tuple(self._channel.getpeername(), self._reqhost)


    @property
    def listening(self):
        """
        True if this is a listening socket, and False otherwise.
        """
        return self._listening


    @property
    def connecting(self):
        """
        True if the socket is in the process of establishing a connection
        but is not yet connected.

        Once the socket is connected, the connecting property will be False,
        but the :attr:`connected` property will be True.
        """
        return self._connecting


    @property
    def connected(self):
        """
        True when the socket is currently connected to a peer.

        When a socket is in the process of :attr:`connecting`, it is not
        considered connected, although it is considered :attr:`alive`.

        .. note::
           This property will not change until a :meth:`read` or :meth:`write`
           is attempted on the socket.  Only then can it be determined if
           the socket has disconnected.

        .. warning::
           When you want to read all data from the socket until it closes,
           you should use the :attr:`readable` property instead.
        """
        return self._channel != None and not self._close_inprogress and not self._listening


    @property
    def alive(self):
        """
        True if the socket is :attr:`connected`, :attr:`listening`, or
        :attr:`connecting`.
        """
        # Unroll these properties: connected or connecting
        return (self._channel != None and not self._close_inprogress) or self._connecting


    @IOChannel.close_on_eof.setter
    def close_on_eof(self, value):
        # close_on_eof makes no sense for sockets and can result in a busy
        # read loop because the readable property will return True even when
        # the socket is dead.  So just prevent this.
        if value != True:
            raise ValueError('close_on_eof cannot be False for sockets')


    @IOChannel.readable.getter
    def readable(self):
        """
        True if :meth:`read` may be called.

        A socket is considered readable when it is :attr:`alive`, or if it's
        closed but there is buffered data to be read.

        Because of the presence of a read buffer, you should test this property
        to determine if you should :meth:`read`, not the :attr:`connected`
        property::

            while socket.readable:
                data = yield socket.read()
                [...]

        .. note::
           A value of True does not mean there **is** data available, but
           rather that there could be and that a :meth:`read` call is possible
           (however that :meth:`read` call may return None, in which case the
           readable property will subsequently be False because the socket is
           disconnected).

        """
        # Note: this property is used in superclass's _update_read_monitor()
        # Unroll these properties: alive or super(readable)
        return (self._channel != None and not self._close_inprogress) or \
               self._connecting or self._read_queue.tell() > 0


    @property
    def buffer_size(self):
        """
        Size of the send and receive socket buffers (SO_SNDBUF and SO_RCVBUF)
        in bytes.

        Setting this to higher values (say 1M) improves performance when
        sending large amounts of data across the socket.  Note that the upper
        bound may be restricted by the kernel.  (Under Linux, this can be tuned
        by adjusting /proc/sys/net/core/[rw]mem_max)
        """
        return self._buffer_size


    @buffer_size.setter
    def buffer_size(self, size):
        self._buffer_size = size
        if self._channel and size:
            self._set_buffer_size(self._channel, size)


    def _set_buffer_size(self, s, size):
        """
        Sets the send and receive buffers of the given socket s to size.
        """
        s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, size)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, size)


    def _make_address_tuple(self, addr, *args):
        """
        Converts an AF_INET6 socket address to a 5- or 6-tuple for use with the
        *local* and *peer* properties.  IPv4-mapped IPv6 addresses are
        converted to standard IPv4 dotted quads.

        On Python 2.6 and later, this returns a namedtuple.
        """
        if isinstance(addr, basestring):
            # Unix socket
            return addr

        if len(addr) == 2:
            addr += (None, None, None)
        else:
            try:
                addr += (if_indextoname(addr[3]),)
            except (ValueError, NotImplementedError):
                addr += (None,)

        # reqhost = args[0] if args else None
        addr += (args[0] if args else None,)
        # ip = addr[0][7:] if addr[0].lower().startswith('::ffff:') else addr[0]
        #addr = (ip,) + addr[1:] + (scope,) + ((reqhost,) if args else ())
        if sys.hexversion < 0x02060000:
            return addr

        fields = 'host port flowinfo scopeid scope' + (' reqhost' if args else '')
        return collections.namedtuple('address', fields)(*addr)



    def listen(self, addr, backlog=5, ipv6=True):
        """
        Set the socket to accept incoming connections.

        :param addr: Binds the socket to this address.  If an int, this
                     specifies a TCP port that is bound on all interfaces; if a
                     str, it is either a Unix socket path or represents a TCP
                     socket when in the form ``[host]:[service][%scope]``.
                     See below for further details.
        :type addr: int, str, or 2- or 4-tuple
        :param backlog: the maximum length to which the queue of pending
                        connections for the socket may grow.
        :type backlog: int
        :param ipv6: if True, will prefer binding to IPv6 addresses if addr is
                     a hostname that contains both AAAA and A records.  If addr
                     is specified as an IP address, this argument does nothing.
        :type ipv6: bool
        :raises: ValueError if *addr* is invalid, or socket.error if the bind fails.

        If *addr* is given as a 4-tuple, it is in the form ``(host, service,
        flowinfo, scope)``.  If passed as a 2-tuple, it is in the form
        ``(host, service)``, and in this case, it is assumed that *flowinfo* and
        *scope* are both 0.  See :meth:`~kaa.Socket.connect` for more
        information.

        If *host* is given as a string, it is treated as a Unix socket path if it
        does not contain ``:``, otherwise it is specified as ``[host]:[service][%scope]``,
        where ``[x]`` indicates that ``x`` is optional, and where:

            * *host* is a hostname, an IPv4 dotted quad, or an IPv6 address
              wrapped in square brackets.  e.g. localhost, 192.168.0.1,
              [3000::1].  If host is not specified, the socket will listen on
              all interfaces.
            * *service* is a service name or port number.  e.g. http, 80
            * *scope* is an interface name or number.  e.g. eth0, 2

        When binding to a link-local address (``fe80::/16``), *scope* must be
        specified.  Relative Unix socket names (those not prefixed with
        ``/``) are created via kaa.tempfile.

        .. warning::

           If the bind address supplied is a hostname rather than an IPv4 or
           IPv6 address, this function will block in order to resolve the
           hostname if the name is not specified in /etc/hosts.  (In other words,
           ``localhost`` is probably safe.)

        Once listening, new connections are automatically accepted, and the
        :attr:`~kaa.Socket.signals.new-client` signal is emitted for each new
        connection.  Callbacks connecting to the signal will receive a new
        Socket object representing the client connection.
        """
        sock = Socket.create_connection(source_address=addr, overwrite=True)
        sock.listen(backlog)
        self._listening = True
        self.wrap(sock, IO_READ | IO_WRITE)


    @threaded()
    def _connect(self, addr, source_address=None, ipv6=True):
        sock = Socket.create_connection(addr, source_address=source_address, ipv6=ipv6)
        # Normalize and store hostname
        addr = Socket.normalize_address(addr)
        if type(addr) == str:
            # Unix socket, just connect.
            self._reqhost = addr
        else:
            self._reqhost = addr[0]

        try:
            self.wrap(sock, IO_READ | IO_WRITE)
        finally:
            self._connecting = False


    def connect(self, addr, source_address=None, ipv6=True):
        """
        Connects to the host specified in address.

        :param addr: Address for a remote host, or a Unix socket.  If a str,
                     it is either a Unix socket path or represents a TCP
                     socket when in the form ``host:service[%scope]``.  See
                     below for further details.
        :type addr: str, or 2- or 4-tuple
        :param ipv6: if True, will connect to the remote host using IPv6 if
                     it is reachable via IPv6.  This is perfectly safe for IPv4
                     only hosts too.  Set this to False if the remote host
                     has a AAAA record and the local host has an IPv6 route to
                     it, but you want to force IPv4 anyway.
        :returns: An :class:`~kaa.InProgress` object.

        If *addr* is given as a 4-tuple, it is in the form ``(host, service,
        flowinfo, scope)``.  If given as a 2-tuple, it is in the form ``(host,
        service)``, and in this case the *flowinfo* and *scope* are assumed to
        be 0.

        The *flowinfo* and *scope* fields are only relevant for IPv6 hosts,
        where they represent the ``sin6_flowinfo`` and ``sin6_scope_id``
        members in :const:`struct sockaddr_in6` in C.  *scope* may be the name
        of an interface (e.g. ``eth0``) or an interface id, and is needed when
        connecting to link-local addresses (``fe80::/16``).

        If *addr* is given as a string, it is treated as a Unix socket path if it
        does not contain ``:``, otherwise it is specified as ``host:service[%scope]``,
        where ``[x]`` indicates that ``x`` is optional, and where:

            * *host* is a hostname, an IPv4 dotted quad, or an IPv6 address
              wrapped in square brackets.  e.g. freevo.org, 192.168.0.1,
              [3000::1]
            * *service* is a service name or port number.  e.g. http, 80
            * *scope* is an interface name or number.  e.g. eth0, 2

        When connecting to a link-local address (fe80::/16), *scope* must be
        specified.  Relative Unix socket names (those not prefixed with ``/``)
        are created via :func:`kaa.tempfile`.

        This function is executed in a thread to avoid blocking.  It therefore
        returns an InProgress object.  If the socket is connected, the InProgress
        is finished with no arguments.  If the connection cannot be established,
        an exception is thrown to the InProgress.
        """
        if self._connecting:
            raise SocketError('connection already in progress')
        elif self.connected:
            raise SocketError('socket already connected')
        self._connecting = True
        return self._connect(addr, source_address, ipv6)


    def wrap(self, sock, mode=IO_READ|IO_WRITE):
        """
        Wraps an existing low-level socket object.

        addr specifies the 4-tuple address corresponding to the socket.
        """
        super(Socket, self).wrap(sock, mode)
        if sock and self._buffer_size:
            self._set_buffer_size(sock, self._buffer_size)
        return self


    def _is_read_connected(self):
        return self._listening or super(Socket, self)._is_read_connected()


    def _set_non_blocking(self):
        self._channel.setblocking(False)


    def _read(self, size):
        return self._channel.recv(size)


    def _write(self, data):
        return self._channel.send(data)


    def _accept(self):
        """
        Accept a new connection and return a new Socket object.
        """
        sock, addr = self._channel.accept()
        # create new Socket from the same class this object is
        client_socket = self._make_new()
        client_socket.wrap(sock, IO_READ | IO_WRITE)
        self.signals['new-client'].emit(client_socket)
        if self._accept_inprogress:
            accept_inprogress = self._accept_inprogress
            self._accept_inprogress = None
            accept_inprogress.finish(client_socket)


    def accept(self):
        if not self._accept_inprogress:
            self._accept_inprogress = InProgress()

        return self._accept_inprogress


    def _handle_read(self):
        if self._listening:
            # Give callbacks on the new-client-connecting signal the chance to
            # abort the autoaccept (if applicable).  If we have an explicit
            # accept() in progress then it can't be aborted, but we still emit
            # anyway for notification purposes.
            aborted = self.signals['new-client-connecting'].emit() == False
            if (self._auto_accept and not aborted) or self._accept_inprogress:
                return self._accept()

        return super(Socket, self)._handle_read()


    def _close(self):
        super(Socket, self)._close()
        self._reqhost = None
        if self._listening and isinstance(self.local, basestring) and self.local.startswith('/'):
            # Remove unix socket if it exists.
            try:
                os.unlink(self.local)
            except OSError:
                pass


    def steal(self, socket):
        if not isinstance(socket, Socket):
            raise TypeError('Can only steal from other sockets')

        self._buffer_size = socket._buffer_size
        return super(Socket, self).steal(socket)
