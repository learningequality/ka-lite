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
            logging.warning("Server error: %s at %s" % (
                str(r.status_code), url))
            if retries == 4:
                logging.info(
                    "Maxed out retries: adding %s to bad urls list" % url)
                r = "server-error"
        elif r.status_code > 399:
            logging.warning("Client error: %s at %s" % (
                str(r.status_code), url))
            logging.info("Adding %s to bad urls list" % url)
            r = "client-error"
            break
        else:
            logging.info("Good request: %s at %s" % (str(r.status_code), url))
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