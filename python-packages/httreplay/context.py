from contextlib import contextmanager
from .patch import start_replay, stop_replay


@contextmanager
def replay(recording_file_name, url_key=None, body_key=None, headers_key=None):
    """
    A simple context manager for using the ``httreplay`` library.

    On entry, patches the various supported HTTP-requesting libraries
    (httplib, requests, urllib3) and starts reading from/writing
    to the replay file on disk.

    On exit, undoes all patches and ends replay.

    Example:

        with replay('/tmp/my_recording.json'):
            ... perform http requests ...

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
    start_replay(
        recording_file_name,
        url_key=url_key,
        body_key=body_key,
        headers_key=headers_key)
    yield
    stop_replay()
