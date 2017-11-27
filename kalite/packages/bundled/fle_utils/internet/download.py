import logging
import os
import requests
import socket
import tempfile


from requests.packages.urllib3.util.retry import Retry
from kalite.updates.settings import DOWNLOAD_SOCKET_TIMEOUT


socket.setdefaulttimeout(DOWNLOAD_SOCKET_TIMEOUT)


logger = logging.getLogger(__name__)


def callback_percent_proxy(callback, start_percent=0, end_percent=100):
    if not callback:
        return None
    percent_range_size = end_percent - start_percent

    def callback_percent_proxy_inner_fn(fraction):
        callback(start_percent + int(fraction * percent_range_size))
    return callback_percent_proxy_inner_fn


def _nullhook(*args, **kwargs):
    pass


def download_file(url, dst=None, callback=None, fp=None, max_retries=5):

    assert not (dst and fp)

    callback = callback or _nullhook

    from requests.adapters import HTTPAdapter

    s = requests.Session()
    
    # Define the way that we do retries.
    # retries = 5
    # backoff = 0.2
    # sum(b * (2 ^ (r - 1)) for r in range(1,6))
    # =2.4 seconds total retry backoff
    # socket timeout is 20 (see above)
    # = 102.4 seconds on an unconnected line
    retries = Retry(
        total=max_retries,
        connect=max_retries,
        read=max_retries,
        backoff_factor=0.2,
    )
    
    s.mount('http://', HTTPAdapter(max_retries=retries))

    # Assuming the KA Lite version is included in user agent because of an
    # intention to create stats on learningequality.org
    from kalite.version import user_agent
    
    # Notice that we deliberate aren't using the ``timeout`` kwarg here, we
    # will allow the stream to hang forever when a connection is disrupted
    # but a download has already started. This is to not have to write "resume"
    # logic on top of our retry logic.
    response = s.get(
        url,
        allow_redirects=True,
        stream=True,
        # timeout=DOWNLOAD_SOCKET_TIMEOUT,
        headers={"user-agent": user_agent()}
    )
    
    response.raise_for_status()

    # Don't do this things until passed the raise_for_status() point
    # If not called with a file pointer or destination, create a new temporary
    # file
    # If a destination is set, then we'll write a file and send back updates
    if dst:
        fp = open(dst, 'wb')
    if not (dst or fp):
        fp, dst = tempfile.mkstemp()[1]

    chunk_size = 1024 * 50 # 50 KB
    for chunk_number, chunk in enumerate(response.iter_content(chunk_size)):
        fp.write(chunk)
        bytes_fetched = chunk_number * chunk_size
        if 'content-length' not in response.headers:
            fraction = 0.0
        elif int(response.headers['content-length']) == 0:
            fraction = 0.0
        else:
            total_size = float(response.headers['content-length'])
            fraction = min(float(bytes_fetched) / total_size, 1.0)
        callback(fraction)

    # Many operations expect a file pointer at 0 after having written the file
    # successfully. For instance if it's passed on to a ZipFile object.
    fp.seek(0)

    # Verify file existence
    dst = fp.name or None
    if dst:
        if os.path.isfile(dst):
            size_on_disk = os.path.getsize(dst)
        else:
            size_on_disk = 0
        if 'content-length' in response.headers:
            size_header = int(response.headers['content-length'])
        size_header = 0
        
        if size_on_disk <=0 or (size_header and size_on_disk != size_header):
            logger.error((
                "Error downloading {url}, incorrect file size, disk full? "
                "Expected {header}, got {disk}").format(
                    url=url,
                    header=size_header,
                    disk=size_header,
                )
            )
            raise RuntimeError("Download failed to write correct file.")

    return response
