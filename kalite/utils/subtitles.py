import logging
import requests

def make_request(headers, url, max_retries=5):
    """Return response from url; retry up to 5 times for server errors.
    When returning an error, return human-readable status code.

    codes: server-error, client-error
    """
    for retries in range(1, 1 + max_retries):
        try:
            r = requests.get(url, headers=headers)
            if r.status_code > 499:
                if retries == max_retries:
                    logging.warn(
                        "Error downloading %s: server-side error (%d)" % (url, r.status_code))
                    r = "server-error"
                    break;
            elif r.status_code > 399:
                logging.warn(
                    "Error downloading %s: client-side error (%d)" % (url, r.status_code))
                r = "client-error"
                break
            # TODO(dylan): if internet connection goes down, we aren't catching
            # that, and things just break
            else:
                break
        except Exception as e:
            logging.warn("Error downloading %s: %s" % (url, e))
    return r
