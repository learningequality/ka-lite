"""
Miscellaneous utility functions (no dependence on non-standard packages, such as Django)

General string, integer, date functions.
"""
import datetime
import json
import os
import errno

from distutils.version import StrictVersion
from sqlitedict import SqliteDict


class InvalidDateFormat(Exception):

    def __str__(value):
        return "Invalid date format. Please format your date (-d) flag like this: 'MM/DD/YYYY'"

class InvalidDirectoryFormat(Exception):

    def __str__(value):
        return "Invalid directory format. Please ensure you are passing in a directory path, not a filepath."


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


def get_host_name():
    """
    Cross-platform way to get the current computer name.
    """
    name = ""
    try:
        name = eval("os.uname()[1]")
    except:
        try:
            name = eval("os.getenv('HOSTNAME', os.getenv('COMPUTERNAME') or '').lower()")
        except:
            name = ""
    return name


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

    v1_parts += ["0"] * (len(v2_parts) - len(v1_parts))
    v2_parts += ["0"] * (len(v1_parts) - len(v2_parts))

    for v1p,v2p in zip(v1_parts,v2_parts):
        cur_diff = int(v1p)-int(v2p)
        if cur_diff:
            return cur_diff

    return 0


# http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
def ensure_dir(path):
    """Create the entire directory path, if it doesn't exist already."""
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            # file already exists
            if not os.path.isdir(path):
                # file exists but is not a directory
                raise OSError(errno.ENOTDIR, "Not a directory: '%s'" % path)
            pass  # directory already exists
        else:
            raise

# http://code.activestate.com/recipes/82465-a-friendly-mkdir/
#def _mkdir(newdir):
#    """works the way a good mkdir should :)
#        - already exists, silently complete
#        - regular file in the way, raise an exception
#        - parent directory(ies) does not exist, make them as well
#    """
#    if os.path.isdir(newdir):
#        pass
#    elif os.path.isfile(newdir):
#        raise OSError("a file with the same name as the desired " \
#                      "dir, '%s', already exists." % newdir)
#    else:
#        head, tail = os.path.split(newdir)
#        if head and not os.path.isdir(head):
#            _mkdir(head)
#        if tail:
#            os.mkdir(newdir)

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


def get_module_source_file(module_name):
    """
    http://stackoverflow.com/questions/247770/retrieving-python-module-path
    http://stackoverflow.com/questions/8718885/import-module-from-string-variable
    """
    module_name.split
    source_file = __import__(module_name, fromlist=[""]).__file__
    if source_file.endswith(".pyc"):
        return source_file[0:-1]
    return source_file


def max_none(data):
    """
    Given a list of data, returns the max... removing None elements first, for comparison "safety".
    """

    # Base case: data is none, then return max of that.
    if not data:
        return max(data)

    non_none_data = []
    for d in data:
        if d is not None:
            non_none_data.append(d)
    return max(non_none_data) if non_none_data else None


def _decode_list(data):
    rv = []
    for item in data:
        if isinstance(item, unicode):
            item = item.encode('utf-8')
        elif isinstance(item, list):
            item = _decode_list(item)
        elif isinstance(item, dict):
            item = json_ascii_decoder(item)
        rv.append(item)
    return rv


def json_ascii_decoder(data):
    """
    TODO: Delete, it doesn't seem to be used anymore

    benjaoming: I don't see how this is more efficient. Letting the JSON
    library load files and parse them with a built-in decoder, probably even
    implemented in C would be much faster.

    A custom JSON decoder that can be passed to json.load/s.  This
    parses strings into str instead of unicode. To use this, pass this
    function to the object_hook keyword param in json.load/s.

    Mainly used to help in encoding issues and memory efficiency.

    """
    rv = {}
    for key, value in data.iteritems():
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        if isinstance(value, unicode):
            value = value.encode('utf-8')
        elif isinstance(value, list):
            value = _decode_list(value)
        elif isinstance(value, dict):
            value = json_ascii_decoder(value)
        rv[key] = value
    return rv


def softload_json(json_filepath, default={}, raises=False, logger=None, errmsg="Failed to read json file"):
    # TODO(benjaoming): What's this? No comment for crazy statement for
    # reference value'ed kwarg :/ default=X is only used in kalite/basetests/tests.py
    # so can easily be removed anyways.
    if default == {}:
        default = {}
    try:
        with open(json_filepath, "r") as fp:
            return json.load(fp, object_hook=json_ascii_decoder)
    # TODO: This is an anti-pattern, never do this. Always expect specific
    # exceptions and handle them in a specific context.
    except Exception as e:
        if logger:
            logger("%s %s: %s" % (errmsg, json_filepath, e))
        if raises:
            raise
        return default


def softload_sqlite_cache(cache_filepath, raises=False):

    try:
        return SqliteDict(cache_filepath)
    except Exception:
        if raises:
            raise
        else:
            return None


def sort_version_list(version_list, reverse):
    """Returns sorted version list - assumes strict version number"""
    version_list.sort(reverse=reverse, key=lambda s: StrictVersion(s))
    return version_list
