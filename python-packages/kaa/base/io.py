# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# io.py - I/O management for the Kaa Framework
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

__all__ = [ 'IO_READ', 'IO_WRITE', 'IO_EXCEPT', 'IOMonitor', 'WeakIOMonitor', 'IOChannel' ]

import sys
import os
import socket
import logging
import time
import fcntl
import re
import errno
import threading
try:
    from io import BytesIO
except ImportError:
    from cStringIO import StringIO as BytesIO

from .utils import property
from .strutils import BYTES_TYPE, UNICODE_TYPE, py3_b, bl
from . import nf_wrapper as notifier
from .callable import WeakCallable
from .core import Object, Signal, CoreThreading
from .thread import MainThreadCallable, threaded, MAINTHREAD
from .async import InProgress, inprogress
from . import main

# get logging object
log = logging.getLogger('kaa.base.core.io')

IO_READ   = 1
IO_WRITE  = 2
IO_EXCEPT = 3

class IOMonitor(notifier.NotifierCallback):
    def __init__(self, callback, *args, **kwargs):
        """
        Creates an IOMonitor to monitor IO activity via the mainloop.

        Once a file descriptor is registered using the
        :meth:`~kaa.IOMonitor.register` method, the given *callback* is invoked
        upon I/O activity.
        """
        super(IOMonitor, self).__init__(callback, *args, **kwargs)
        self.ignore_caller_args = True


    def register(self, fd, condition = IO_READ):
        """
        Register the IOMonitor to a specific file descriptor.

        The IOMonitor is registered with the notifier, which means that the
        notifier holds a reference to the IOMonitor until it is explicitly
        unregistered (or until the file descriptor is closed).

        :param fd: The file descriptor to monitor.
        :type fd: File descriptor or any file-like object
        :param condition: IO_READ, IO_WRITE, or IO_EXCEPT
        """
        if self.active:
            if fd != self._id or condition != self._condition:
                raise ValueError('Existing file descriptor already registered with this IOMonitor.')
            return
        if not CoreThreading.is_mainthread():
            # Ultimately we need to make sure the main loop gets woken up when
            # we register the new fd so that it gets monitored right away.  The
            # most straightforward way is to reinvoke this function from the
            # main loop.
            return MainThreadCallable(self.register)(fd, condition)
        notifier.socket_add(fd, self, condition-1)
        self._condition = condition
        # Must be called _id to correspond with base class.
        self._id = fd


    def unregister(self):
        """
        Unregister the IOMonitor
        """
        if not self.active:
            return
        if not CoreThreading.is_mainthread():
            return MainThreadCallable(self.unregister)()
        notifier.socket_remove(self._id, self._condition-1)
        super(IOMonitor, self).unregister()



class WeakIOMonitor(notifier.WeakNotifierCallback, IOMonitor):
    """
    IOMonitor using weak references for the callback.

    Any previously registered file descriptor will become unregistered from
    the notifier when the callback (or any arguments) are destroyed.
    """
    pass


class IOChannel(Object):
    """
    Base class for read-only, write-only or read-write stream-based
    descriptors such as Socket and Process.  Implements logic common to
    communication over such channels such as async read/writes and read/write
    buffering.

    It may also be used directly with file descriptors or (probably less
    usefully) file-like objects.  e.g. ``IOChannel(file('somefile'))``

    :param channel: file descriptor to wrap into an IOChannel
    :type channel: integer file descriptor, file-like object, or other IOChannel
    :param mode: indicates whether the channel is readable, writable, or both.
    :type mode: bitmask of kaa.IO_READ and/or kaa.IO_WRITE
    :param chunk_size: maximum number of bytes to be read in from the channel
                       at a time; defaults to 1M.
    :param delimiter: string used to split data for use with readline; defaults
                      to '\\\\n'.

    Writes may be performed to an IOChannel that is not yet open.  These writes
    will be queued until the queue size limit (controlled by the
    :attr:`~kaa.IOChannel.queue_size` property) is reached, after which an
    exception will be raised.  The write queue will be written to the channel
    once it becomes writable.

    Reads are asynchronous and non-blocking, and may be performed using two
    possible approaches:

        1. Connecting a callback to the :attr:`~kaa.IOChannel.signals.read`
           or :attr:`~kaa.IOChannel.signals.readline` signals.
        2. Invoking the :meth:`~kaa.IOChannel.read` or
           :meth:`~kaa.IOChannel.readline` methods, which return
           :class:`~kaa.InProgress` objects.

    It is not possible to use both approaches with readline.  (That is, it
    is not permitted to connect a callback to the *readline* signal and
    subsequently invoke the :meth:`~kaa.IOChannel.readline` method when the
    callback is still connected.)

    However, :meth:`~kaa.IOChannel.read` and :meth:`~kaa.IOChannel.readline`
    will work predictably when a callback is connected to the *read* signal.
    Such a callback always receives all data from the channel once connected,
    but will not interfere with (or "steal" data from) calls to read() or
    readline().

    Data is not consumed from the channel if no one is interested in reads
    (that is, when there are no read() or readline() calls in progress, and
    there are no callbacks connected to the *read* and *readline* signals).
    This is necessary for flow control.

    Data is read from the channel in chunks, with the maximum chunk being
    defined by the :attr:`~kaa.IOChannel.queue_size` property.  Unlike other
    APIs, read() does not block and will not consume all data to the end of the
    channel, but rather returns between 0 and *chunk_size* bytes when it
    becomes available.  If read() returns a zero-byte string, it means the
    channel is closed.  (Here, "returns X" means the :class:`~kaa.InProgress`
    object read() actually returns is finished with X.)

    In order for readline to work properly, a read queue is maintained, which
    may grow up to *queue_size*.  See the :meth:`~kaa.IOChannel.readline` method
    for more details.
    """
    __kaasignals__ = {
        'read':
            '''
            Emitted for each chunk of data read from the channel.

            .. describe:: def callback(chunk, ...)

               :param chunk: data read from the channel
               :type chunk: str

            When a callback is connected to the *read* signal, data is automatically
            read from the channel as soon as it becomes available, and the signal
            is emitted.

            It is allowed to have a callback connected to the *read* signal
            and simultaneously use the :meth:`~kaa.IOChannel.read` and
            :meth:`~kaa.IOChannel.readline` methods.
            ''',

        'readline':
            '''
            Emitted for each line read from the channel.

            .. describe:: def callback(line, ...)

               :param line: line read from the channel
               :type line: str

            It is not allowed to have a callback connected to the *readline* signal
            and simultaneously use the :meth:`~kaa.IOChannel.readline` method.

            Refer to :meth:`~kaa.IOChannel.readline` for more details.
            ''',

        'closed':
            '''
            Emitted when the channel is closed.

            .. describe:: def callback(expected, ...)

               :param expected: True if the channel is closed because
                                :meth:`~kaa.IOChannel.close` was called.
               :type expected: bool
            '''
    }

    def __init__(self, channel=None, mode=IO_READ|IO_WRITE, chunk_size=1024*1024, delimiter='\n'):
        super(IOChannel, self).__init__()
        self.delimiter = delimiter
        self._write_queue = []
        # Read queue used for read() and readline(), and 'readline' signal.
        self._read_queue = BytesIO()
        self._read_queue_lock = threading.RLock()
        # Number of bytes each queue (read and write) are limited to.
        self._queue_size = 1024*1024
        self._chunk_size = chunk_size
        self._queue_close = False
        self._close_inprogress = None
        self._close_on_eof = True
        self._eof = False

        # Internal signals for read() and readline()  (these are different from
        # the same-named public signals as they get emitted even when data is
        # None.  When these signals get updated, we call _update_read_monitor
        # to register the read IOMonitor.
        # FIXME: should do the same for closed as well, for write-only sockets.
        cb = WeakCallable(self._update_read_monitor)
        self._read_signal = Signal(cb)
        self._readline_signal = Signal(cb)
        self.signals['read'].changed_cb = cb
        self.signals['readline'].changed_cb = cb

        # These variables hold the IOMonitors for monitoring; we only allocate
        # a monitor when the channel is connected to avoid a ref cycle so that
        # disconnected channels will get properly deleted when they are not
        # referenced.
        self._rmon = None
        self._wmon = None

        self.wrap(channel, mode)


    def __repr__(self):
        clsname = self.__class__.__name__
        if not hasattr(self, '_channel') or not self._channel:
            return '<kaa.%s - disconnected>' % clsname
        return '<kaa.%s fd=%s>' % (clsname, self.fileno)


    @property
    def channel(self):
        """
        The original object this IOChannel is wrapping.

        This may be a file object, socket object, file descriptor, etc.,
        depending what was passed during initialization or to :meth:`wrap`.

        This is None if the channel is closed.
        """
        return self._channel


    @property
    def alive(self):
        """
        True if the channel exists and is open.
        """
        # If the channel is closed, self._channel will be None.
        return self._channel != None and not self._close_inprogress


    @property
    def readable(self):
        """
        True if :meth:`read` may be called.

        The channel is *readable* if it's open and its mode has IO_READ, or if
        the channel is closed but a :meth:`read` call would still succeed (due
        to buffered data).

        .. note::
           A value of True does not mean there **is** data available, but
           rather that there could be and that a :meth:`read` call is possible
           (however that :meth:`read` call may return None, in which case the
           readable property will subsequently be False).
        """
        return self._mode & IO_READ and \
               ((self.alive and not self._eof) or self._read_queue.tell() > 0)


    @property
    def writable(self):
        """
        True if :meth:`write` may be called.

        (However, if you pass too much data to write() such that the write
        queue limit is exceeded, the write will fail.)
        """
        # By default, this is always True regardless if the channel is open, so
        # long as there is space available in the write queue, but subclasses
        # may want to override.
        return self._mode & IO_WRITE and self.write_queue_used < self._queue_size


    @property
    def fileno(self):
        """
        The file descriptor (integer) for this channel, or None if no channel
        has been set.
        """
        try:
            return self._channel.fileno()
        except (ValueError, AttributeError):
            # AttributeError: probably not a file object (doesn't have fileno() anyway)
            # ValueError: probably "I/O operation on a closed file"
            return self._channel


    @property
    def chunk_size(self):
        """
        Number of bytes to attempt to read from the channel at a time.

        The default is 1M.  A 'read' signal is emitted for each chunk read from
        the channel.  (The number of bytes read at a time may be less than the
        chunk size, but will never be more.)
        """
        return self._chunk_size


    @chunk_size.setter
    def chunk_size(self, size):
        self._chunk_size = size


    @property
    def queue_size(self):
        """
        The size limit in bytes for the read and write queues.

        Each queue can consume at most this size plus the chunk size.  Setting
        a value does not affect any data currently in any of the the queues.
        """
        return self._queue_size


    @queue_size.setter
    def queue_size(self, value):
        self._queue_size = value


    @property
    def write_queue_used(self):
        """
        The number of bytes queued in memory to be written to the channel.
        """
        # XXX: this is not terribly efficient when the write queue has
        # many elements.  We may decide to keep a separate counter.
        return sum(len(data) for data, inprogress in self._write_queue)


    @property
    def read_queue_used(self):
        """
        The number of bytes in the read queue.

        The read queue is only used if either readline() or the readline signal
        is.
        """
        return self._read_queue.tell()

    @property
    def delimiter(self):
        """
        String used to split data for use with :meth:`readline`.

        Delimiter may also be a list of strings, in which case any one of the
        elements in the list will be used as a delimiter.  For example, if you
        want to delimit based on either \\\\r or \\\\n, specify ['\\\\r', '\\\\n'].
        """
        return self._delimiter


    @delimiter.setter
    def delimiter(self, value):
        self._delimiter = value
        if isinstance(value, (UNICODE_TYPE, BYTES_TYPE)):
            self._delimiter_encoded = py3_b(value)
        elif isinstance(value, (list, tuple)):
            regexp = bl('|').join(py3_b(x) for x in value)
            self._delimiter_encoded = re.compile(regexp)
        else:
            raise ValueError('delimiter must be a string, bytes, or sequence of strings or bytes')


    @property
    def mode(self):
        """
        Whether the channel is read-only, or read/write.

        A bitmask of IO_READ and/or IO_WRITE.
        """
        return self._mode


    @property
    def close_on_eof(self):
        """
        Whether the channel automatically closes when EOF is encountered or on
        unexpected exceptions.

        The channel is considered EOF when a read returns an empty string. A
        write that fails due to IOError or OSError will also close the channel
        if this property is True.

        This behaviour makes sense for stream-based channels (e.g. a
        subprocess or socket), but may not for file-based channels.  The
        default is True unless the underlying wrapped channel object contains
        a ``seek`` method, in which case it is treated as a file and this
        property is False.  In either case it can be overridden by explicitly
        setting this property.
        """
        return self._close_on_eof

    @close_on_eof.setter
    def close_on_eof(self, value):
        self._close_on_eof = value


    def _is_read_connected(self):
        """
        Returns True if an outside caller is interested in reads (not readlines).
        """
        return len(self._read_signal) != 0  or \
               (len(self.signals['read']) != 0 and not self._eof)


    def _is_readline_connected(self):
        """
        Returns True if an outside caller is interested in readlines (not reads).
        """
        return not len(self._readline_signal) == len(self.signals['readline']) == 0


    def _update_read_monitor(self, signal=None, action=None):
        """
        Update read IOMonitor to register or unregister based on if there are
        any handlers attached to the read signals.  If there are no handlers,
        there is no point in reading data from the channel since it will go
        nowhere.  This also allows us to push back the read buffer to the OS.

        We must call this immediately after reading a block, and not defer
        it until the end of the mainloop iteration via a timer in order not
        to lose incoming data between read() calls.
        """
        if action == Signal.CONNECTED and len(self.signals['read']) == 1:
            # First signal connected to the global read.  If there is anything
            # in the read queue (data accumulated from a readline) emit it
            # now.
            #
            # FIXME: corner case: if the callback is removed and readded, the
            # same data could get emitted.
            data = self._read_queue.getvalue()
            if data:
                self.signals['read'].emit(data)
        if not (self._mode & IO_READ) or not self._rmon:
            return
        elif not self._is_read_connected() and not self._is_readline_connected():
            self._rmon.unregister()
        elif not self._rmon.active:
            self._rmon.register(self.fileno, IO_READ)


    def _set_non_blocking(self):
        """
        Low-level call to set the channel non-blocking.  Can be overridden by
        subclasses.
        """
        flags = fcntl.fcntl(self.fileno, fcntl.F_GETFL)
        fcntl.fcntl(self.fileno, fcntl.F_SETFL, flags | os.O_NONBLOCK)


    def wrap(self, channel, mode):
        """
        Make the IOChannel represent a new descriptor or file-like object.

        This is implicitly called by the initializer.  If the IOChannel is
        already wrapping another channel, it will be closed before the given
        one is wrapped.

        :param channel: file descriptor to wrap into the IOChannel
        :type channel: integer file descriptor, file-like object, or
                       other IOChannel
        :param mode: indicates whether the channel is readable, writable,
                     or both.  Only applies to file descriptor channels or
                     IOChannel objects; for file-like objects, the underlying
                     channel's mode will be assumed.
        :type mode: bitmask of kaa.IO_READ and/or kaa.IO_WRITE
        """
        if hasattr(self, '_channel') and self._channel:
            # Wrapping a new channel while an existing one is open, so close
            # the existing one.
            self.close(immediate=True)

        if isinstance(channel, IOChannel):
            # Given channel is itself another IOChannel.  Wrap its underlying
            # channel (file descriptor or other file-like object).
            channel = channel._channel
            self._close_on_eof = channel._close_on_eof
            self._eof = channel._close_on_eof
        else:
            # For normal seekable files, we want to disable close_on_eof
            # behaviour so we're closer to the normal file API.  Test seeking
            # on the given channel and if it doesn't raise an exception, we can
            # set close_on_eof to False.  We can't reliably determine if a channel
            # is seekable without actually trying a seek, because streams could be
            # wrapped in file-like objects with fdopen.
            try:
                fd = channel if isinstance(channel, int) else channel.fileno()
                os.lseek(fd, 0, os.SEEK_CUR)
                self._close_on_eof = False
            except (AttributeError, TypeError, IOError, OSError):
                self._close_on_eof = True
            self._eof = False

        self._channel = channel
        self._mode = 0
        self._clear_read_queue()
        if not channel:
            return self
        elif hasattr(channel, 'mode'):
            if 'r' in channel.mode:
                self._mode |= IO_READ
            if 'w' in channel.mode:
                self._mode |= IO_WRITE
            if 'a' in channel.mode or '+' in channel.mode:
                self._mode = IO_READ | IO_WRITE
        else:
            self._mode = mode
        self._set_non_blocking()

        if self._rmon:
            self._rmon.unregister()
            self._rmon = None
        if self._wmon:
            self._wmon.unregister()
            self._wmon = None

        if self._mode & IO_READ:
            self._rmon = IOMonitor(self._handle_read)
            self._update_read_monitor()
        if self._mode & IO_WRITE:
            self._wmon = IOMonitor(self._handle_write)
            if self._write_queue:
                self._wmon.register(self.fileno, IO_WRITE)

        # Disconnect channel on shutdown.
        #
        # XXX: actually, don't.  If a Process object has a stop command, we
        # need stdin alive so we can send it.  Even if it doesn't have a stop
        # command, closing the stdin pipe to child processes seems to sometimes
        # do undesirable things.  For example, MPlayer will leave one of its
        # threads running, even though the main thread dies.)
        #
        # If it turns out we do need a shutdown handler for IOChannels,
        # make it opt-in and clearly document why.
        #
        #main.signals['shutdown'].connect_weak(self.close)
        return self


    def _clear_read_queue(self):
        with self._read_queue_lock:
            self._read_queue.seek(0)
            self._read_queue.truncate()


    def _find_delim(self, buf, start=0):
        """
        Returns the position in the buffer where the first delimiter is found.
        The index position includes the delimiter.  If the delimiter is not
        found, None is returned.
        """
        if type(self._delimiter_encoded) == BYTES_TYPE:
            idx = buf.find(self._delimiter_encoded, start)
            return idx + len(self._delimiter_encoded) if idx >= 0 else None

        # Delimiter is a list, so find any one of them.
        m = self._delimiter_encoded.search(buf, start)
        return m.end() if m else None


    def _pop_line_from_read_queue(self):
        """
        Pops a line (plus delimiter) from the read queue.  If the delimiter
        is not found in the queue, returns None.
        """
        with self._read_queue_lock:
            s = self._read_queue.getvalue()
            idx = self._find_delim(s)
            if idx is None:
                if (not self._channel or self._eof) and s:
                    # Channel is closed or EOF and there's data left in the read
                    # queue. Just return what's left.
                    self._clear_read_queue()
                    return s
                else:
                    # Wait for more data that contains the delimiter
                    return

            self._clear_read_queue()
            self._read_queue.write(s[idx:])
            return s[:idx]


    def _abort_read_inprogress(self, exc, signal, ip):
        signal.disconnect(ip)
        self._update_read_monitor()


    def _async_read(self, signal):
        """
        Common implementation for read() and readline().
        """
        if not self._channel:
            raise IOError(errno.EBADF, 'I/O operation on closed file')
        elif not (self._mode & IO_READ):
            raise IOError(9, 'Cannot read on a write-only channel')
        elif not self.readable:
            # channel is not readable.  Return an InProgress pre-finished
            # with None
            return InProgress().finish(None)

        ip = inprogress(signal)
        # If this InProgress is aborted, we need to disconnect it from the
        # read signal and make sure we update the read monitor.  But we do
        # this connection weakly to prevent the circular reference (notice we
        # pass ip as args here) so that if the caller is no longer interested
        # in the returned InProgress and it is destroyed, we stop listening
        # for read events on the socket.
        ip.signals['abort'].connect_weak(self._abort_read_inprogress, signal, ip)
        return ip


    def read(self):
        """
        Reads a chunk of data from the channel.

        :returns: An :class:`~kaa.InProgress` object. If the InProgress is
                  finished with the empty string, it means that no data
                  was collected and the channel was closed (or the channel
                  was already closed when read() was called).

        It is therefore possible to busy-loop by reading on a closed channel::

            while True:
                data = yield channel.read()
                # Or: channel.read().wait()

        So the return value of read() should be checked.  Alternatively,
        the :attr:`readable` property could be tested::

            while channel.readable:
                 data = yield process.read()

        """
        with self._read_queue_lock:
            if self._read_queue.tell() > 0:
                s = self._read_queue.getvalue()
                self._clear_read_queue()
                return InProgress().finish(s)

        return self._async_read(self._read_signal)


    def readline(self):
        """
        Reads a line from the channel.

        The line delimiter is included in the string to avoid ambiguity.  If no
        delimiter is present then either the read queue became full or the
        channel was closed before a delimiter was received.

        :returns: An :class:`~kaa.InProgress` object. If the InProgress is
                  finished with the empty string, it means that no data
                  was collected and the channel was closed (or the channel
                  was already closed when readline() was called).

        Data from the channel is read and queued in until the delimiter (\\\\n by
        default, but may be changed by the :attr:`delimiter`
        property) is found.  If the read queue size exceeds the queue limit,
        then the InProgress returned here will be finished prematurely with
        whatever is in the read queue, and the read queue will be purged.

        This method may not be called when a callback is connected to the
        IOChannel's readline signal.  You must use either one approach or the
        other.
        """
        if self._is_readline_connected() and len(self._readline_signal) == 0:
            # Connecting to 'readline' signal _and_ calling readline() is
            # not supported.  It's unclear how to behave in this case.
            raise RuntimeError('Callback currently connected to readline signal')

        line = self._pop_line_from_read_queue()
        if line:
            return InProgress().finish(line)
        return self._async_read(self._readline_signal)


    def _read(self, size):
        """
        Low-level call to read from channel.  Can be overridden by subclasses.
        Must return a string of at most size bytes, or the empty string or
        None if no data is available.
        """
        try:
            return self._channel.read(size)
        except AttributeError:
            return os.read(self.fileno, size)


    def _handle_read(self):
        """
        IOMonitor callback when there is data to be read from the channel.

        This callback is only registered when we know the user is interested in
        reading data (by connecting to the read or readline signals, or calling
        read() or readline()).  This is necessary for flow control.
        """
        exc = None
        try:
            data = self._read(self._chunk_size)
        except (IOError, socket.error) as e:
            exc = sys.exc_info()
            if len(e.args) != 2:
                # IOError and socket.error typically have (errno, msg) args but
                # occasionally don't (e.g. 'File not open for reading').  Reraise
                # before attempting to unpack args.
                raise
            errno, msg = e.args
            if errno == 11:
                # Resource temporarily unavailable -- we are trying to read
                # data on a socket when none is available.
                return
            # If we're here, then the socket is likely disconnected.
            log.exception('some error')
            data = ''
        except Exception:
            exc = sys.exc_info()
            log.exception('%s._handle_read failed, closing socket', self.__class__.__name__)
            data = ''

        #log.debug2('IOChannel read data: channel=%s fd=%s len=%d', self._channel, self.fileno, len(data))

        if not data:
            self._eof = True
            if self._close_on_eof:
                # No data, channel is closed.  IOChannel.close will emit signals
                # used for read() and readline() with any data left in the read
                # queue in order to finish any InProgress waiting.
                return self.close(immediate=True, expected=False)

        # _read_signal is for InProgress objects waiting on the next read().
        if len(self._read_signal):
            if exc:
                self._read_signal.emit(*exc)
            else:
                self._read_signal.emit(data)
        if data:
            self.signals['read'].emit(data)

        with self._read_queue_lock:
            if len(self._readline_signal):
                # Handle a readline() call
                if self.read_queue_used + len(data) > self._queue_size:
                    # This data chunk would exceed the read queue limit.  We
                    # instead emit whatever's in the read queue, and then start
                    # it over with this chunk.
                    # TODO: it's possible this chunk contains the delimiter we've
                    # been waiting for.  If so, we could salvage things.
                    line = self._read_queue.getvalue()
                    self._clear_read_queue()
                    self._read_queue.write(data)
                else:
                    self._read_queue.write(data)
                    line = self._pop_line_from_read_queue()

                if line is not None:
                    self._readline_signal.emit(line)
                elif self._eof:
                    if exc:
                        self._readline_signal.throw(*exc)
                    else:
                        # EOF with a readline() waiting.  Send it the empty string.
                        self._readline_signal.emit('')
            elif len(self.signals['readline']):
                # Handle global readline signal by looping through read queue and
                # emit all lines individually.
                queue = self._read_queue.getvalue() + data
                self._clear_read_queue()

                lines, last, idx = [], 0, self._find_delim(queue)
                while True:
                    # If idx is None, it will slice to the end.
                    lines.append(queue[last:idx])
                    if idx is None:
                        break
                    last = idx
                    idx = self._find_delim(queue, last)

                if self._find_delim(lines[-1]) is None:
                    # Queue did not end with delimiter, so push the remainder back.
                    self._read_queue.write(lines.pop())

                for line in lines:
                    self.signals['readline'].emit(line)


        # Update read monitor if necessary.  If there are no longer any
        # callbacks left on any of the read signals (most likely _read_signal
        # or _readline_signal), we want to prevent _handle_read() from being
        # called, otherwise next time read() or readline() is called, we will
        # have lost that data.
        self._update_read_monitor()


    def _write(self, data):
        """
        Low-level call to write to the channel  Can be overridden by subclasses.
        Must return number of bytes written to the channel.
        """
        return os.write(self.fileno, data)


    def _abort_write_inprogress(self, exc, data, ip):
        try:
            self._write_queue.remove((data, ip))
        except ValueError:
            # Too late to abort.
            return False


    def write(self, data):
        """
        Writes the given data to the channel.

        :param data: the data to be written to the channel.
        :type data: string

        :returns: An :class:`~kaa.InProgress` object which is finished when the
                  given data is fully written to the channel.  The InProgress
                  is finished with the number of bytes sent in the last write
                  required to commit the given data to the channel.  (This may
                  not be the actual number of bytes of the given data.)

                  If the channel closes unexpectedly before the data was
                  written, an IOError is thrown to the InProgress.

        It is not required that the channel be open in order to write to it.
        Written data is queued until the channel open and then flushed.  As
        writes are asynchronous, all written data is queued.  It is the
        caller's responsibility to ensure the internal write queue does not
        exceed the desired size by waiting for past write() InProgress to
        finish before writing more data.

        If a write does not complete because the channel was closed
        prematurely, an IOError is thrown to the InProgress.
        """
        if not self._channel:
            raise IOError(errno.EBADF, 'I/O operation on closed file')
        elif not (self._mode & IO_WRITE):
            raise IOError(9, 'Cannot write to a read-only channel')
        elif not self.writable:
            raise IOError(9, 'Channel is not writable')
        elif self.write_queue_used + len(data) > self._queue_size:
            raise ValueError('Data would exceed write queue limit')
        elif not isinstance(data, BYTES_TYPE):
            raise ValueError('data must be bytes, not unicode')

        ip = InProgress()
        if data:
            ip.signals['abort'].connect(self._abort_write_inprogress, data, ip)
            self._write_queue.append((data, ip))
            if self._channel and self._wmon and not self._wmon.active:
                self._wmon.register(self.fileno, IO_WRITE)
        else:
            # We're writing the null string, nothing really to do.  We're
            # implicitly done.
            ip.finish(0)
        return ip


    def _handle_write(self):
        """
        IOMonitor callback when the channel is writable.  This callback is not
        registered then the write queue is empty, so we only get called when
        there is something to write.
        """
        if not self._write_queue:
            # Can happen if a write was aborted.
            return

        try:
            while self._write_queue:
                data, inprogress = self._write_queue.pop(0)
                sent = self._write(data)
                log.debug2('IOChannel write data: channel=%s fd=%s len=%d (of %d)',
                           self._channel, self.fileno, sent, len(data))
                if sent != len(data):
                    # Not all data was able to be sent; push remaining data
                    # back onto the write buffer.
                    self._write_queue.insert(0, (data[(sent if sent >= 0 else 0):], inprogress))
                    break
                else:
                    # All data is written, finish the InProgress associated
                    # with this write.
                    inprogress.finish(sent)

            if not self._write_queue:
                if self._queue_close:
                    return self.close(immediate=True)
                self._wmon.unregister()

        except Exception, e:
            tp, exc, tb = sys.exc_info()
            if tp in (OSError, IOError, socket.error):
                if e.args[0] == 11:
                    # Resource temporarily unavailable -- we are trying to write
                    # data to a socket which is not ready.  To prevent a busy loop
                    # (mainloop will keep calling us back) we sleep a tiny
                    # bit.  It's admittedly a bit kludgy, but it's a simple
                    # solution to a condition which should not occur often.
                    self._write_queue.insert(0, (data, inprogress))
                    time.sleep(0.001)
                    return
                else:
                    if self._close_on_eof:
                        # Close, which also throws to any other pending
                        # InProgress writes.
                        self.close(immediate=True, expected=False)
                    # Normalize exception into an IOError.
                    tp, exc = IOError, IOError(*e.args)

            # Throw the current exception to the InProgress for this write.
            # If nobody is listening for it, it will eventually get logged
            # as unhandled.
            inprogress.throw(tp, exc, tb)

            # XXX: this seems to be necessary in order to get the unhandled
            # InProgress to log, but I've no idea why.
            del inprogress


    def _close(self):
        """
        Low-level call to close the channel.  Can be overridden by subclasses.
        """
        try:
            self._channel.close()
        except AttributeError:
            os.close(self.fileno)


    # Among other things, this method invokes callbacks so ensure it runs in
    # the main thread.
    @threaded(MAINTHREAD)
    def close(self, immediate=False, expected=True):
        """
        Closes the channel.

        :param immediate: if False and there is data in the write buffer, the
                          channel is closed once the write buffer is emptied.
                          Otherwise the channel is closed immediately and the
                          *closed* signal is emitted.
        :type immediate: bool
        """
        log.debug('IOChannel closed: channel=%s, immediate=%s, fd=%s', self, immediate, self.fileno)
        if not self._rmon and not self._wmon:
            # already closed
            return

        if not self._close_inprogress:
            # Set _closing flag in case any callbacks connected to any pending
            # read/write InProgress objects test the 'alive' property, which
            # we want to be False.  Yet we don't want to actually _close()
            # before finishing the pending InProgress in case _close() raises,
            # which we want to let propagate.
            self._close_inprogress = InProgress()

        if not immediate and self._write_queue:
            # Immediate close not requested and we have some data left
            # to be written, so defer close until after write queue
            # is empty.
            self._queue_close = True
            return self._close_inprogress

        if self._rmon:
            self._rmon.unregister()
        if self._wmon:
            self._wmon.unregister()
        self._rmon = None
        self._wmon = None
        self._queue_close = False


        # If there Finish any InProgress waiting on read() or readline() with whatever
        # is left in the read queue.
        with self._read_queue_lock:
            if len(self._read_signal):
                s = self._read_queue.getvalue()
                self._read_signal.emit(s)
            if len(self._readline_signal):
                line = self._pop_line_from_read_queue()
                if line:
                    self._readline_signal.emit(line)

        # Throw IOError to any pending InProgress in the write queue
        for data, inprogress in self._write_queue:
            if len(inprogress):
                # Somebody cares about this InProgress, so we need to finish
                # it.
                inprogress.throw(IOError, IOError(9, 'Channel closed prematurely'), None)
        del self._write_queue[:]

        try:
            self._close()
        except (IOError, socket.error), (errno, msg):
            # Channel may already be closed, which is ok.
            if errno != 9:
                # It isn't, this is some other error, so reraise exception.
                self._close_inprogress.throw()
                raise
        except Exception:
            # Finish the close InProgress with any other exception and
            # reraise.
            self._close_inprogress.throw()
            raise
        else:
            self._close_inprogress.finish(expected)
        finally:
            self._channel = None
            self._close_inprogress = None
            self._mode = 0

            self.signals['closed'].emit(expected)
            # We aren't attaching to 'shutdown' in wrap() after all.  Comment
            # out for now.
            #main.signals['shutdown'].disconnect(self.close)


    def steal(self, channel):
        """
        Steal all state from the given channel, assuming control over the underlying
        file descriptor or socket.

        :param channel: the channel to steal from
        :type channel: :class:`~kaa.IOChannel`
        :return: self

        The use-case for this method is primarily to convert one type of
        IOChannel into another.  For example, it's possible to convert a
        standard :class:`~kaa.Socket` into a :class:`~kaa.TLSSocket` in the
        middle of a session.  This method returns ``self`` so that this idiom
        is possible::

            from kaa.net.tls import TLSSocket
            sock = TLSSocket().steal(sock)

        This method is similar to :meth:`wrap`, but additionally
        all state is moved from the supplied IOChannel, including read/write
        queues, and all callbacks connected to signals are added to ``self``,
        and removed from ``channel``.

        Once stolen, the given ``channel`` is rendered basically inert.
        """
        self.wrap(channel, channel.mode)

        self._delimiter = channel.delimiter
        self._write_queue = channel._write_queue
        self._read_queue = channel._read_queue
        self._queue_size = channel._queue_size
        self._chunk_size = channel._chunk_size
        self._queue_close = channel._queue_close

        # Generate new queues on the channel object whose fd we are stealing, since
        # we stole its queues too.
        channel._write_queue = []
        channel._read_queue = BytesIO()
        channel._channel = None

        def clone(src, dst):
            [dst.connect(cb) for cb in src.callbacks]
            # FIXME: need to take care of abort callbacks for IP
            src.disconnect_all()

        clone(channel._read_signal, self._read_signal)
        clone(channel._readline_signal, self._readline_signal)
        clone(channel.signals['read'], self.signals['read'])
        clone(channel.signals['readline'], self.signals['readline'])

        return self
