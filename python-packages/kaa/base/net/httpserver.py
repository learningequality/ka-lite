# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# httpserver.py - Simple HTTP server based on kaa
# -----------------------------------------------------------------------------
# This module provides a RequestHandler and a TCPServer that together
# work as simple HTTP server for kaa.
#
# -----------------------------------------------------------------------------
# Copyright 2012 Dirk Meyer
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
import os
import logging
import socket
import BaseHTTPServer
import SocketServer
import shutil
import urlparse
import json
import cgi

# kaa imports
import kaa
from .. import nf_wrapper as notifier

# get logging object
log = logging.getLogger('kaa')

class ThreadedHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    RequestHandler.
    """

    def do_POST(self):
        ctype, pdict = cgi.parse_header(self.headers.getheader('content-type'))
        if ctype != 'application/json':
            log.error('HTTP/POST not JSON: %s' % ctype)
            self.send_response(500)
            self.end_headers()
            return
        length = int(self.headers.getheader('content-length'))
        data = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
        parse_result = urlparse.urlparse(self.path)
        try:
          for path, callback, ctype, encoding in self.server._get_handler:
            if path == parse_result.path or \
                    (parse_result.path.startswith(path) and path.endswith('/')):
                path = parse_result.path[len(path):]
                result = []
                for key in data.keys():
                    calls = json.loads(key)
                    if not isinstance(calls, (list, tuple)):
                        calls = (calls,)
                    for c in calls:
                        result.append(kaa.MainThreadCallable(callback)(path, **c).wait())
                if len(result) == 1:
                    result = json.dumps(result[0])
                else:
                    result = json.dumps(result)
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", len(result))
                # self.send_header("Content-Encoding", encoding)
                self.end_headers()
                self.wfile.write(result)
                return
        except:
            self.send_response(500)
            log.exception('server error')
            return

    def do_GET(self):
        """
        Serve a GET request.
        """
        callback = None
        parse_result = urlparse.urlparse(self.path)
        for path, callback, ctype, encoding in self.server._get_handler:
            if path == parse_result.path or \
                    (parse_result.path.startswith(path) and path.endswith('/')):
                path = parse_result.path[len(path):]
                try:
                    attributes = {}
                    for key, value in urlparse.parse_qs(parse_result.query).items():
                        if isinstance(value, (list, tuple)):
                            if len(value) == 0:
                                attributes[key] = True
                            elif len(value) == 1:
                                attributes[key] = value[0]
                            else:
                                attributes[key] = value
                        else:
                            attributes[key] = value
                    result = kaa.MainThreadCallable(callback)(path, **attributes).wait()
                except:
                    self.send_response(500)
                    log.exception('server error')
                    return
                if result is None:
                    # return 404
                    self.send_response(404)
                    self.end_headers()
                    return
                # we need content, content type and content encoding
                # as result if not already provided when registering
                # the callback
                if ctype is None or encoding is None:
                    # return must be a list with the actual content as
                    # first item and ctype and encoding if missing
                    # following.
                    result = list(result)
                    if encoding is None:
                        encoding = result.pop()
                    if ctype is None:
                        ctype = result.pop()
                    result = result[0]
                if ctype == "application/json":
                    result = json.dumps(result)
                self.send_response(200)
                self.send_header("Content-type", ctype)
                self.send_header("Content-Length", len(result))
                self.send_header("Content-Encoding", encoding)
                self.end_headers()
                self.wfile.write(result)
                return
        if self.path in self.server._static:
            self.send_response(200)
            self.end_headers()
            f = open(self.server._static[self.path])
            shutil.copyfileobj(f, self.wfile)
            f.close()
            return
        abspath = os.path.abspath(self.path)
        for path, dirname in self.server._directories:
            if abspath.startswith(path):
                fname = os.path.join(dirname, abspath[len(path)+1:])
                if os.path.isfile(fname):
                    self.send_response(200)
                    self.end_headers()
                    f = open(fname)
                    shutil.copyfileobj(f, self.wfile)
                    f.close()
                    return
        self.send_response(404)
        self.end_headers()
        return

    def log_message(self, format, *args):
        """
        Dump log messages to the used logging object
        """
        if len(args) != 3 or args[1] != '200':
            log.info(format, *args)


class HTTPServer(SocketServer.ThreadingTCPServer):
    """
    HTTPServer
    """
    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass=ThreadedHTTPRequestHandler,
                 bind_and_activate=True):
        """
        Create the HTTPServer
        """
        self._get_handler = []
        self._static = {}
        self._directories = []
        SocketServer.ThreadingTCPServer.__init__(
            self, server_address, RequestHandlerClass, bind_and_activate)

    def process_request_thread(self, request, client_address):
        """
        Rewrite of process_request_thread from the ThreadingTCPServer
        handling socket.error by ignoring it.
        """
        try:
            self.finish_request(request, client_address)
            self.shutdown_request(request)
        except socket.error:
            # the other side did not want to wait long enough
            pass
        except:
            self.handle_error(request, client_address)
            self.shutdown_request(request)

    def __handle_request(self, f):
        """
        Wrapper around _handle_request_noblock for pynotifier
        """
        self._handle_request_noblock()
        return True

    def serve_forever(self):
        """
        Hook the server into pynotifier
        """
        notifier.socket_add(self.fileno(), self.__handle_request)

    def add_handler(self, path, callback, ctype=None, encoding=None):
        """
        Add a handler for path
        """
        self._get_handler.append((path, callback, ctype, encoding))

    def add_json_handler(self, path, callback):
        """
        Add a handler for path
        """
        self._get_handler.append((path, callback, 'application/json', 'utf-8'))

    def add_static(self, path, filename):
        """
        Add a static page from filename
        """
        if os.path.isdir(filename):
            self._directories.append((path, filename))
        else:
            self._static[path] = filename
