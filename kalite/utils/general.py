"""
Miscellaneous utility functions (no dependence on non-standard packages, such as Django) 

General string, integer, date functions.
"""
import datetime
import os


class InvalidDateFormat(Exception):

    def __str__(value):
        return "Invalid date format. Please format your date (-d) flag like this: 'MM/DD/YYYY'"


def break_into_chunks(bigiterator, chunksize=500):
    """
    Given an iterator, separates the iterator into a list of iterators,
    each broken into a discrete size.
    """
    biglist = list(bigiterator)
    return [biglist[i:i+chunksize] for i in range(0, len(biglist), chunksize)]


def isnumeric(obj):
    """
    Returns whether an object is itself numeric, or can be converted to numeric
    """

    try:
        float(obj)
        return True
    except:
        return False


def datediff(*args, **kwargs):
    """
    Given two datetime.datetimes, returns the total difference between them (in the units specified).
    Given a single timedelta, returns the delta in the units specified.

    This is akin to the timedelta.total_seconds() function, with two differences:
    (a) That function is only available in Python 2.7+
    (b) That function has units of seconds available only.
    """
    assert len(args) in [1, 2], "Must specify two dates or one timedelta"

    units = kwargs.get("units", None)
    if len(args)==2:
        tdelta = args[0] - args[1]
    elif len(args) == 1:
        tdelta = args[0]

    diff_secs = tdelta.days*24*60*60 + tdelta.seconds + tdelta.microseconds/1000000.

    # Put None first, so checks are minimized
    if units in [None, "second", "seconds"]:
        return diff_secs
    elif units in ["microsecond", "microseconds"]:
        return diff_secs*1000000
    elif units in ["minute", "minutes"]:
        return diff_secs/60.
    elif units in ["hour", "hours"]:
        return diff_secs/3600.
    elif units in ["day", "days"]:
        return diff_secs/(24*3600.)
    elif units in ["week", "weeks"]:
        return diff_secs/(7*24*3600.)
    else:
        raise NotImplementedError("Unrecognized units: '%s'" % units)


def version_diff(v1, v2):
    """
    Diff is the integer difference between the most leftward part of the versions that differ.
    If the versions are identical, the method returns zero.
    If v1 is earlier than v2, the method returns negative.
    If v1 is later than v2, the method returns positive.
    If EITHER IS NONE, then we return none.

    Examples:

    version_diff(None, "0.9.4") returns None

    version_diff("0.9.2", "0.9.4") returns -2
    version_diff("0.9.4", "0.9.4") returns 0
    version_diff("0.9.4", "0.9.2") returns 2

    version_diff("0.9", "1.0") returns -1 (0-1)
    version_diff("0.3", "0.7") returns -4 (3-7)
    """

    #
    if v1 is None or v2 is None:
        return None

    v1_parts = v1.split(".")
    v2_parts = v2.split(".")
    if len(v1_parts) != len(v2_parts):
        raise Exception("versions must have the same number of components (periods)")

    for v1p,v2p in zip(v1_parts,v2_parts):
        cur_diff = int(v1p)-int(v2p)
        if cur_diff:
            return cur_diff

    return 0


def ensure_dir(path):
    """Create the entire path, if it doesn't exist already."""
    path_parts = path.split("/")
    full_path = "/"
    for part in path_parts:
        if part is not '':
            full_path += part + "/"
            if not os.path.exists(full_path):
                os.makedirs(full_path)


def convert_date_input(date_to_convert):
    """Convert from MM/DD/YYYY to Unix timestamp"""
    if date_to_convert:
        try:
            converted_date = datetime.datetime.strptime(
                date_to_convert, '%m/%d/%Y')
        except:
            raise InvalidDateFormat()
        return converted_date
    else:
        return date_to_convert
