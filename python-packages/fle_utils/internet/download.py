import os
import requests
import socket
import sys
import tempfile
from requests.utils import default_user_agent

socket.setdefaulttimeout(20)


class DownloadCancelled(Exception):

    def __str__(self):
        return "Download has been cancelled"


class URLNotFound(Exception):
    pass


def callback_percent_proxy(callback, start_percent=0, end_percent=100):
    if not callback:
        return None
    percent_range_size = end_percent - start_percent

    def callback_percent_proxy_inner_fn(fraction):
        callback(start_percent + int(fraction * percent_range_size))
    return callback_percent_proxy_inner_fn


def _reporthook(numblocks, blocksize, filesize, url=None):
    base = os.path.basename(url)
    if filesize <= 0:
        filesize = blocksize
    try:
        percent = min((numblocks * blocksize * 100) / filesize, 100)
    except:
        percent = 100
    if numblocks != 0:
        sys.stdout.write("\b" * 40)
    sys.stdout.write("%-36s%3d%%" % (base, percent))
    if percent == 100:
        sys.stdout.write("\n")


def _nullhook(*args, **kwargs):
    pass


def download_file(url, dst=None, callback=None):
    if sys.stdout.isatty():
        callback = callback or _reporthook
    else:
        callback = callback or _nullhook
    dst = dst or tempfile.mkstemp()[1]

    # Assuming the KA Lite version is included in user agent because of an
    # intention to create stats on learningequality.org
    from kalite.version import VERSION as KALITE_VERSION
    response = requests.get(
        url,
        allow_redirects=True,
        stream=True,
        headers={"user-agent": "ka-lite/%s " % KALITE_VERSION + default_user_agent()}
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
    return response


def make_request(headers, url, max_retries=5):
    """Return response from url; retry up to 5 times for server errors.
    When returning an error, return human-readable status code.

    codes: server-error, client-error, unexpected-error
    """
    assert max_retries >= 0, "max_retries must be non-negative."  # guarantees response will never be None

    response = None
    last_error = None
    for retries in range(1, 1 + max_retries):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code >= 500:
                if retries == max_retries:
                    logging.warn("Unexpected Error downloading %s: server-side error (%d)" % (
                        url, response.status_code,
                    ))
                    response = "server-error"
                    break
            elif response.status_code >= 400:
                logging.debug("Error downloading %s: client-side error (%d)" % (
                    url, response.status_code,
                ))
                response = "client-error"
                break
            else:
                # Success case
                break

        except Exception as e:
            if response is None:
                response = "unexpected-error"
            cur_error = unicode(e.args[0])
            if not last_error or last_error != cur_error:
                logging.warn(u"Unexpected Error downloading %s: %s" % (url, cur_error))
            last_error = cur_error

    return response
