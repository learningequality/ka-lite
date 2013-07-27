import datetime
import logging
import os
import requests
import time


class InvalidDateFormat(Exception):

    def __str__(value):
        return "Invalid date format. Please format your date (-d) flag like this: 'MM/DD/YYYY'"


def make_request(headers, url, max_retries=5):
    """Return response from url; retry up to 5 times for server errors.
    When returning an error, return human-readable status code.
    
    codes: server-error, client-error
    """
    for retries in range(1, 1+max_retries):
        try:
            r = requests.get(url, headers=headers)
            if r.status_code > 499:
                if retries == max_retries:
                    logging.warn("Error downloading %s: server-side error (%d)" % (url, r.status_code))
                    r = "server-error"
                    break;
            elif r.status_code > 399:
                logging.warn("Error downloading %s: client-side error (%d)" % (url, r.status_code))
                r = "client-error"
                break
            # TODO(dylan): if internet connection goes down, we aren't catching that, and things just break
            else:
                break
        except Exception as e:
            time.sleep(1) # HELP: is this ok on the server?
            logging.warn("Error downloading %s: %s" % (url, e))
    return r

def convert_date_input(date_to_convert):
    # convert from MM/DD/YYYY to Unix timestamp to compare against JSON file
    if date_to_convert:
        try:
            converted_date = datetime.datetime.strptime(
                date_to_convert, '%m/%d/%Y')
        except:
            raise InvalidDateFormat()
        return converted_date
    else:
        return date_to_convert


def setup_logging(name):
    FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
    logging.basicConfig(format=FORMAT)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger


def file_already_exists(path):
    file_exists = False
    if os.path.exists(path):
        file_exists = True
    return file_exists


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)