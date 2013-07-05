def break_into_chunks(bigiterator, chunksize=500):
    """
    Given an iterator, separates the iterator into a list of iterators,
    each broken into a discrete size.
    """
    biglist = list(bigiterator)
    return [biglist[i:i+chunksize] for i in range(0, len(biglist), chunksize)]

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


if __name__ == "__main__":
    import datetime
    d1 = datetime.datetime.now()
    d2 = datetime.datetime(2000, 12, 1)
    print datediff(d1, d2, units="seconds")
    print datediff(d1-d2)