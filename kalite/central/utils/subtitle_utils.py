import datetime
import logging
import os
import time

import requests

import paths_and_headers

class InvalidDateFormat(Exception):

    def __str__(value):
        return "Invalid date format. Please format your date (-d) flag like this: 'MM/DD/YYYY'"


def make_request(url):
    """Return response from url; retry up to 5 times for server errors; when returning an error, return human-readable status code."""
    
    headers = paths_and_headers.headers

    for retries in range(1, 5):
        r = requests.get(url, headers=headers)
        time.sleep(1) # HELP: is this ok on the server?
        if r.status_code > 499:
            if retries == 4:
                r = "server-error"
        elif r.status_code > 399:
            r = "client-error"
            break
        else:
            break
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