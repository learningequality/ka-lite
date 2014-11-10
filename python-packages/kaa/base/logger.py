# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# logger.py - Updates to the Python logging module
# -----------------------------------------------------------------------------
# This module 'fixes' the Python logging module to accept fixed string and
# unicode arguments. It will also make sure that there is a logging handler
# defined when needed.
#
# -----------------------------------------------------------------------------
# Copyright 2006-2013 Dirk Meyer, Jason Tackaberry
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

# Python imports
import logging
import logging.handlers
import sys
import os

# kaa.base imports
if sys.hexversion >= 0x02060000:
    # Python 2.6 and 3.1's logger does the right thing with Unicode.  Actually,
    # Python 2.6.2 is broken if you pass it an encoded string (it tries to call
    # encode() on it before writing to the stream).  This problem is fixed with
    # at least 2.6.5, but either version behaves sanely if you give it unicode
    # strings.
    from .strutils import py3_str as logger_str_convert
else:
    # On the other hand, Python 2.5's logging module is less robust with unicode,
    # so convert arguments to non-unicode strings.
    from .strutils import py3_b as logger_str_convert


class Logger(logging.Logger):
    """
    A custom logger from Kaa that implements a debug2() method using a new
    DEBUG2 log level, addresses unicode bugs in the logging module of various
    Python versions, and adds a new method ensureRootHandler()
    """
    def ensureRootHandler(self, fmt=None, datefmt=None, replace=False):
        """
        Ensures the root logger has a handler attached.  This is a convenience
        method similar to logging.basicConfig().

        :param fmt: the log format string; if None a sensible default is used
        :param datefmt: the date format string; if None a sensible default is used
        :param replace: if True, removes all existing root handlers before
                        adding a new handler
        :returns: self

        This method returns self to allow this idiom::

            log = logging.getLogger('app').ensureRootHandler()
        """
        if replace:
            # delete current handlers
            for l in self.root.handlers:
                self.root.removeHandler(l)
        elif len(self.root.handlers) > 0:
            # there is already a logger and replace=False, skipping
            return self

        fmt = fmt or '%(asctime)s [%(levelname)s] %(module)s(%(lineno)s): %(message)s'
        formatter = logging.Formatter(fmt, datefmt)
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        self.root.addHandler(handler)
        return self


    def makeRecord(self, name, level, fn, lno, msg, args, *_args, **_kwargs):
        """
        This custom makeRecord ensures unicode (whether unicode objects or
        encoded strings) is handled correctly, providing consistent
        behaviour across several Python versions.
        """
        # ensure msg and args are unicode (python 2.6+) or non-unicode (python 2.5)
        msg = logger_str_convert(msg)
        args = tuple(logger_str_convert(x) for x in args)

        # Allow caller to override default location by specifying a 2-tuple
        # (filename, lineno) as 'location' in the extra dict.
        extra = _args[2]
        if extra and 'location' in extra:
            fn, lno = extra['location']

        # call original function
        return logging.Logger.makeRecord(self, name, level, fn, lno, msg, args, *_args, **_kwargs)


    def debug2(self, msg, *args, **kwargs):
        if self.isEnabledFor(logging.DEBUG2):
            self._log(logging.DEBUG2, msg, args, **kwargs)


def add_stdout_handler():
    """
    Add simple stdout logging handler and formater to the root logger
    """
    formatter = logging.Formatter('%(levelname)s %(module)s(%(lineno)s): %(message)s')
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


def add_file_handler(filename, maxbytes=1000000, count=2):
    """
    Add simple file logging handler and formater to the root logger
    """
    if not os.path.isdir(os.path.dirname(filename)):
        os.makedirs(os.path.dirname(filename))
    formatter = logging.Formatter('%(asctime)s %(levelname)-8s [%(name)6s] %(filename)s %(lineno)s: %(message)s')
    handler = logging.handlers.RotatingFileHandler(filename, maxBytes=maxbytes, backupCount=count)
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)


logging.DEBUG2 = 5
logging.addLevelName(logging.DEBUG2, 'DEBUG2')
logging.setLoggerClass(Logger)

logging.add_stdout_handler = add_stdout_handler
logging.add_file_handler = add_file_handler
