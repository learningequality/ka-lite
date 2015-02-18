import httplib
from .replay_settings import ReplaySettings
from stubs.base import ReplayHTTPConnection, ReplayHTTPSConnection


#------------------------------------------------------------------------------
# Hold onto original objects for un-patching later
#------------------------------------------------------------------------------

_original_http_connection = httplib.HTTPConnection
_original_https_connection = httplib.HTTPSConnection

try:
    import requests
    import requests.packages.urllib3.connectionpool
    _original_requests_verified_https_connection = \
        requests.packages.urllib3.connectionpool.VerifiedHTTPSConnection
    _original_requests_http_connection = \
        requests.packages.urllib3.connectionpool.HTTPConnection
    if requests.__version__.startswith('2'):
        _original_requests_https_connection_pool_cls = \
            requests.packages.urllib3.connectionpool.HTTPSConnectionPool.ConnectionCls
        _original_requests_http_connection_pool_cls = \
            requests.packages.urllib3.connectionpool.HTTPConnectionPool.ConnectionCls
except ImportError:
    pass

try:
    import urllib3
    _original_urllib3_verified_https_connection = \
        urllib3.connectionpool.VerifiedHTTPSConnection
    _original_urllib3_http_connection = urllib3.connectionpool.HTTPConnection
except ImportError:
    pass


#------------------------------------------------------------------------------
# Patching methods
#------------------------------------------------------------------------------

def _patch_httplib(settings):
    httplib.HTTPSConnection = httplib.HTTPS._connection_class = \
        ReplayHTTPSConnection
    httplib.HTTPSConnection._replay_settings = settings
    httplib.HTTPConnection = httplib.HTTP._connection_class = \
        ReplayHTTPConnection
    httplib.HTTPConnection._replay_settings = settings


def _patch_requests(settings):
    try:
        import requests
        import requests.packages.urllib3.connectionpool
        from .stubs.requests_stubs import ReplayRequestsHTTPSConnection
        requests.packages.urllib3.connectionpool.VerifiedHTTPSConnection = \
            ReplayRequestsHTTPSConnection
        requests.packages.urllib3.connectionpool.VerifiedHTTPSConnection.\
            _replay_settings = settings
        requests.packages.urllib3.connectionpool.HTTPConnection = \
            ReplayHTTPConnection
        requests.packages.urllib3.connectionpool.HTTPConnection.\
            _replay_settings = settings
        if requests.__version__.startswith('2'):
            requests.packages.urllib3.connectionpool.HTTPConnectionPool.ConnectionCls = \
                ReplayHTTPConnection
            requests.packages.urllib3.connectionpool.HTTPConnectionPool.ConnectionCls.\
                _replay_settings = settings
            requests.packages.urllib3.connectionpool.HTTPSConnectionPool.ConnectionCls = \
                ReplayRequestsHTTPSConnection
            requests.packages.urllib3.connectionpool.HTTPSConnectionPool.ConnectionCls.\
                _replay_settings = settings
    except ImportError:
        pass


def _patch_urllib3(settings):
    try:
        import urllib3.connectionpool
        from .stubs.urllib3_stubs import ReplayUrllib3HTTPSConnection
        urllib3.connectionpool.VerifiedHTTPSConnection = \
            ReplayUrllib3HTTPSConnection
        urllib3.connectionpool.VerifiedHTTPSConnection._replay_settings = \
            settings
        urllib3.connectionpool.HTTPConnection = ReplayHTTPConnection
        urllib3.connectionpool.HTTPConnection._replay_settings = settings
    except ImportError:
        pass


def start_replay(replay_file_name, **kwargs):
    """
    Start using the ``httreplay`` library.

    Patches the various supported HTTP-requesting libraries
    (httplib, requests, urllib3) and starts reading from/writing
    to the replay file on disk.

    Because HTTP requests and responses may contain sensitive data,
    and because they may vary in inconsequential ways that you may
    wish to ignore, the ``httreplay`` provides several hooks to "filter"
    the request contents to generate a stable key suitable for your
    needs. Some example "filters" may be found in the ``utils.py`` file,
    which is currently a grab-bag of things the ``httreplay`` author
    has found useful, no matter how silly.

    :param replay_file_name: The file from which to load and save replays.
    :type replay_file_name: string
    :param url_key: Function that generates a stable key from a URL.
    :type url_key: function
    :param body_key: Function that generates a stable key from a
        request body.
    :type body_key: function
    :param headers_key: Function that generates a stable key from a
        dictionary of headers.
    :type headers_key: function
    """
    settings = ReplaySettings(replay_file_name, **kwargs)
    _patch_httplib(settings)
    _patch_requests(settings)
    _patch_urllib3(settings)


#------------------------------------------------------------------------------
# Un-patching methods
#------------------------------------------------------------------------------

def _unpatch_httplib():
    httplib.HTTPSConnection = httplib.HTTPS._connection_class = \
        _original_https_connection
    httplib.HTTPConnection = httplib.HTTP._connection_class = \
        _original_http_connection


def _unpatch_requests():
    try:
        import requests
        import requests.packages.urllib3.connectionpool
        requests.packages.urllib3.connectionpool.VerifiedHTTPSConnection = \
            _original_requests_verified_https_connection
        requests.packages.urllib3.connectionpool.HTTPConnection = \
            _original_requests_http_connection
        if requests.__version__.startswith('2'):
            requests.packages.urllib3.connectionpool.HTTPSConnectionPool.ConnectionCls = \
                _original_requests_https_connection_pool_cls
            requests.packages.urllib3.connectionpool.HTTPConnectionPool.ConnectionCls = \
                _original_requests_http_connection_pool_cls
    except ImportError:
        pass


def _unpatch_urllib3():
    try:
        import urllib3.connectionpool
        urllib3.connectionpool.VerifiedHTTPSConnection = \
            _original_urllib3_verified_https_connection
        urllib3.connectionpool.HTTPConnection = \
            _original_urllib3_http_connection
    except ImportError:
        pass


def stop_replay():
    """
    Remove all patches installed by the ``httreplay`` library and end replay.
    """
    _unpatch_httplib()
    _unpatch_requests()
    _unpatch_urllib3()
