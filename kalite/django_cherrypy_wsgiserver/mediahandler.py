#!/usr/bin/env python
# -*- coding: utf-8 -*-
# fix these up
import os, stat, mimetypes

from django.utils.http import http_date


class BlockIterator(object):
    # Vlada Macek Says:
    # September 29th, 2009 at 14:42
    # You’re handing the static files by

    #                output = [fp.read()]
    #                fp.close()

    # which causes entire content is loaded to the memory (and not only once
    # by my observation). This is unacceptable for large files. I found this
    # to be much more memory & CPU efficient:

    def __init__(self, fp):
        self.fp = fp

    def __iter__(self):
           return self

    def next(self):
        chunk = self.fp.read(20*1024)
        if chunk:
            return chunk
        self.fp.close()
        raise StopIteration

class MediaHandler( object ):

    def __init__( self, media_root ):
        self.media_root = media_root

    def __call__( self, environ, start_response ):

        def done( status, headers, output ):
            start_response( status, headers.items() )
            return output

        path_info = environ['PATH_INFO']
        if path_info[0] == '/':
            path_info = path_info[1:]

        file_path = os.path.normpath( os.path.join( self.media_root, path_info ) )

        # prevent escaping out of paths below media root (e.g. via "..")
        if not file_path.startswith( self.media_root ):
            status = '401 UNAUTHORIZED'
            headers = {'Content-type': 'text/plain'}
            output = ['Permission denied: %s' % file_path]
            return done( status, headers, output )

        if not os.path.exists( file_path ):
            status = '404 NOT FOUND'
            headers = {'Content-type': 'text/plain'}
            output = ['Page not found: %s' % file_path]
            return done( status, headers, output )

        try:
            fp = open( file_path, 'rb' )
        except IOError:
            status = '401 UNAUTHORIZED'
            headers = {'Content-type': 'text/plain'}
            output = ['Permission denied: %s' % file_path]
            return done( status, headers, output )

        # This is a very simple implementation of conditional GET with
        # the Last-Modified header. It makes media files a bit speedier
        # because the files are only read off disk for the first request
        # (assuming the browser/client supports conditional GET).

        mtime = http_date( os.stat(file_path)[stat.ST_MTIME] )
        headers = {'Last-Modified': mtime}
        if environ.get('HTTP_IF_MODIFIED_SINCE', None) == mtime:
            status = '304 NOT MODIFIED'
            output = []
        else:
            status = '200 OK'
            mime_type = mimetypes.guess_type(file_path)[0]
            if mime_type:
                headers['Content-Type'] = mime_type

            #output = [fp.read()]
            # fp.close()
            output = BlockIterator(fp)

        return done( status, headers, output )

