import os
import requests
import socket
import sys
import tempfile


from requests.packages.urllib3.util.retry import Retry


socket.setdefaulttimeout(20)


class URLNotFound(Exception):
    pass


def callback_percent_proxy(callback, start_percent=0, end_percent=100):
    if not callback:
        return None
    percent_range_size = end_percent - start_percent

    def callback_percent_proxy_inner_fn(fraction):
        callback(start_percent + int(fraction * percent_range_size))
    return callback_percent_proxy_inner_fn


def _nullhook(*args, **kwargs):
    pass


def download_file(url, dst=None, callback=None, max_retries=5):
    if sys.stdout.isatty():
        callback = callback or _nullhook
    else:
        callback = callback or _nullhook
    dst = dst or tempfile.mkstemp()[1]

    
    from requests.adapters import HTTPAdapter

    s = requests.Session()
    
    retries = Retry(
        total=max_retries,
        backoff_factor=0.1,
    )
    
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # Assuming the KA Lite version is included in user agent because of an
    # intention to create stats on learningequality.org
    from kalite.version import user_agent
    response = s.get(
        url,
        allow_redirects=True,
        stream=True,
        headers={"user-agent": user_agent()}
    )
    # If a destination is set, then we'll write a file and send back updates
    if dst:
        chunk_size = 1024
        with open(dst, 'wb') as fd:
            for chunk_number, chunk in enumerate(response.iter_content(chunk_size)):
                fd.write(chunk)
                bytes_fetched = chunk_number * chunk_size
                if 'content-length' not in response.headers:
                    fraction = 0.0
                elif int(response.headers['content-length']) == 0:
                    fraction = 0.0
                else:
                    total_size = float(response.headers['content-length'])
                    fraction = min(float(bytes_fetched) / total_size, 1.0)
                callback(fraction)
        # Verify file existence
        if (
            not os.path.isfile(dst) or
            "content-length" not in response.headers or
            not os.path.getsize(dst) == int(response.headers['content-length'])
        ):
            raise URLNotFound("URL was not found, tried: {}".format(url))

    return response
