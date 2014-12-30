class ReplaySettings(object):
    """Captures settings for the current replay session."""
    def __init__(self, replay_file_name, url_key=None, body_key=None,
                 headers_key=None, allow_network=True):
        """
        Configure the ``httreplay`` library.

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
        :param allow_network: Whether to allow outbound network calls in
            the absence of saved data. Defaults to True.
        :type allow_network: boolean
        """
        self.replay_file_name = replay_file_name
        self.url_key = url_key
        self.body_key = body_key
        self.headers_key = headers_key
        self.allow_network = allow_network
