from httplib import HTTPConnection, HTTPSConnection, HTTPMessage
from cStringIO import StringIO
import logging
import quopri
import zlib

from ..recording import ReplayRecordingManager


logger = logging.getLogger(__name__)


class ReplayError(Exception):
    """Generic error base class for the httreplay library."""
    pass


class ReplayConnectionHelper:
    """
    Mixin that provides the ability to serialize and deserialize
    requests and responses into a recording.
    """
    def __init__(self):
        self.__fake_send = False
        self.__recording_data = None

    # Some hacks to manage the presence (or not) of the connection's
    # socket. Requests 2.x likes to set settings on the socket, but
    # only checks whether the connection hasattr('sock') -- not whether
    # the sock itself is None (which is actually its default value,
    # and which httplib likes to see.) Yeesh.
    def __socket_del(self):
        if hasattr(self, 'sock') and (self.sock is None):
            del self.sock

    def __socket_none(self):
        if not hasattr(self, 'sock'):
            self.sock = None

    @property
    def __recording(self):
        """Provide the current recording, or create a new one if needed."""
        recording = self.__recording_data
        if not recording:
            recording = self.__recording_data = \
                ReplayRecordingManager.load(
                    self._replay_settings.replay_file_name)
        return recording

    # All httplib requests use the sequence putrequest(), putheader(),
    # then endheaders() -> _send_output() -> send()

    def putrequest(self, method, url, **kwargs):
        self.__socket_none()
        # Store an incomplete request; this will be completed when
        # endheaders() is called.
        self.__request = dict(
            method=method,
            _url=url,
            _headers={},
        )
        return self._baseclass.putrequest(self, method, url, **kwargs)

    def putheader(self, header, *values):
        self.__socket_none()
        # Always called after putrequest() so the dict is prepped.
        val = self.__request['_headers'].get(header)
        # http://www.w3.org/Protocols/rfc2616/rfc2616-sec4.html#sec4.2
        val = '' if val is None else val + ','
        val += '\r\n\t'.join(values)
        self.__request['_headers'][header] = val
        return self._baseclass.putheader(self, header, *values)

    def endheaders(self, message_body=None):
        self.__socket_del()
        # If a key generator for the URL is provided, use it.
        # Otherwise, simply use the URL itself as the URL key.
        url = self.__request.pop('_url')
        if self._replay_settings.url_key:
            url_key = self._replay_settings.url_key(url)
        else:
            url_key = url

        # If a key generator for the headers is provided, use it.
        # Otherwise, simply use the headers directly.
        headers = self.__request.pop('_headers')
        if self._replay_settings.headers_key:
            headers_key = self._replay_settings.headers_key(headers)
        else:
            headers_key = headers

        # message_body can be a file; handle that before generating
        # body_key
        if message_body and callable(getattr(message_body, 'read', None)):
            body_content = message_body.read()
            message_body = StringIO(body_content)  # for continuity
        else:
            body_content = message_body

        # If a key generator for the body is provided, use it.
        # Otherwise, simply use the body itself as the body key.
        if body_content is not None and self._replay_settings.body_key:
            body_key = self._replay_settings.body_key(body_content)
        else:
            body_key = body_content

        self.__request.update(dict(
            # method already present
            url=url_key,
            headers=headers_key,
            body=body_key,
            host=self.host,
            port=self.port,
        ))

        # endheaders() will eventually call send()
        logstr = '%(method)s %(host)s:%(port)s/%(url)s' % self.__request
        if self.__request in self.__recording:
            logger.debug("ReplayConnectionHelper found %s", logstr)
            self.__fake_send = True
        else:
            logger.debug("ReplayConnectionHelper trying %s", logstr)
        # result = self._baseclass.endheaders(self, message_body)
        result = self._baseclass.endheaders(self)
        self.__fake_send = False
        return result

    def send(self, msg):
        if not self.__fake_send:
            self.__socket_none()
            return self._baseclass.send(self, msg)

    def getresponse(self, buffering=False):
        """
        Provide a response from the current recording if possible.
        Otherwise, perform the network request.  This function ALWAYS
        returns ReplayHTTPResponse() regardless so it's consistent between
        initial recording and later.
        """
        self.__socket_none()
        replay_response = self.__recording.get(self.__request)

        if replay_response:
            # Not calling the underlying getresponse(); do the same cleanup
            # that it would have done.  However since the cleanup is on
            # class-specific members (self.__state and self.__response) this
            # is the easiest way.
            self.close()

        elif self._replay_settings.allow_network:
            logger.debug("ReplayConnectionHelper calling %s.getresponse()", self._baseclass.__name__)

            response = self._baseclass.getresponse(self)
            replay_response = ReplayHTTPResponse.make_replay_response(response)
            self.__recording[self.__request] = replay_response
            ReplayRecordingManager.save(
                self.__recording,
                self._replay_settings.replay_file_name)

        else:
            logger.debug("ReplayConnectionHelper 418 (allow_network=False)")

            replay_response = dict(
                status=dict(code=418, message="I'm a teapot"),
                headers={},
                body_quoted_printable='Blocked by allow_network=3DFalse')

        return ReplayHTTPResponse(replay_response, method=self.__request['method'])

    def close(self):
        self.__socket_none()
        self._baseclass.close(self)


class ReplayHTTPConnection(ReplayConnectionHelper, HTTPConnection):
    """Generic HTTPConnection with replay."""
    _baseclass = HTTPConnection

    def __init__(self, *args, **kwargs):
        HTTPConnection.__init__(self, *args, **kwargs)
        ReplayConnectionHelper.__init__(self)


class ReplayHTTPSConnection(ReplayConnectionHelper, HTTPSConnection):
    """Generic HTTPSConnection with replay."""
    _baseclass = HTTPSConnection

    def __init__(self, *args, **kwargs):
        # I overrode the init and copied a lot of the code from the parent
        # class because when this happens, HTTPConnection has been replaced
        # by ReplayHTTPConnection,  but doing it here lets us use the original
        # one.
        HTTPConnection.__init__(self, *args, **kwargs)
        ReplayConnectionHelper.__init__(self)
        self.key_file = kwargs.pop('key_file', None)
        self.cert_file = kwargs.pop('cert_file', None)


class ReplayHTTPResponse(object):
    """
    A replay response object, with just enough functionality to make
    the various HTTP/URL libraries out there happy.
    """
    __text_content_types = (
        'text/',
        'application/json',
    )

    def __init__(self, replay_response, method=None):
        self.reason = replay_response['status']['message']
        self.status = replay_response['status']['code']
        self.version = None
        if 'body_quoted_printable' in replay_response:
            self._content = quopri.decodestring(replay_response['body_quoted_printable'])
        else:
            self._content = replay_response['body'].decode('base64')
        self.fp = StringIO(self._content)

        msg_fp = StringIO('\r\n'.join('{}: {}'.format(h, v)
            for h, v in replay_response['headers'].iteritems()))
        self.msg = HTTPMessage(msg_fp)
        self.msg.fp = None  # httplib does this, okay?

        length = self.msg.getheader('content-length')
        self.length = int(length) if length else None

        # Save method to handle HEAD specially as httplib does
        self._method = method

    @classmethod
    def make_replay_response(cls, response):
        """
        Converts real response to replay_response dict which can be saved
        and/or used to initialize a ReplayHTTPResponse.
        """
        replay_response = {}
        body = response.read()  # undecoded byte string

        # Add body to replay_response, either as quoted printable for
        # text responses or base64 for binary responses.
        if response.getheader('content-type', '') \
                .startswith(cls.__text_content_types):
            if response.getheader('content-encoding') in ['gzip', 'deflate']:
                # http://stackoverflow.com/questions/2695152
                body = zlib.decompress(body, 16 + zlib.MAX_WBITS)
                del response.msg['content-encoding']
                # decompression changes the length
                if 'content-length' in response.msg:
                    response.msg['content-length'] = str(len(body))
            replay_response['body_quoted_printable'] = quopri.encodestring(body)
        else:
            replay_response['body'] = body.encode('base64')

        replay_response.update(dict(
            status=dict(code=response.status, message=response.reason),
            headers=dict(response.getheaders())))
        return replay_response

    def close(self):
        self.fp = None

    def isclosed(self):
        return self.fp is None

    def read(self, amt=None):
        """
        The important parts of HTTPResponse.read()
        """
        if self.fp is None:
            return ''

        if self._method == 'HEAD':
            self.close()
            return ''

        if self.length is not None:
            amt = min(amt, self.length)

        # StringIO doesn't like read(None)
        s = self.fp.read() if amt is None else self.fp.read(amt)
        if not s:
            self.close()

        if self.length is not None:
            self.length -= len(s)
            if not self.length:
                self.close()

        return s

    def getheader(self, name, default=None):
        return self.msg.getheader(name, default)

    def getheaders(self):
        return self.msg.items()
