# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# dateutils.py - Date/time utility functions and objects.
# -----------------------------------------------------------------------------
# Copyright 2009-2012 Dirk Meyer, Jason Tackaberry
#
# Please see the file AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------

from datetime import datetime, tzinfo, timedelta
import email.utils
import calendar
import time

__all__ = ['utc', 'local', 'TZAny', 'from_rfc822', 'to_timestamp', 'now', 'utcnow', 'today']


# UTC and Local tzinfo classes, more or less from the python docs.

class TZUTC(tzinfo):
    'UTC timezone'
    ZERO = timedelta(0)
    tzname = lambda self, dt: 'UTC'
    utcoffset = lambda self, dt: TZUTC.ZERO
    dst = lambda self, dt: TZUTC.ZERO
 

class TZLocal(tzinfo):
    'DST-aware local time zone'
    STDOFFSET = timedelta(seconds = -time.timezone)
    DSTOFFSET = timedelta(seconds = -time.altzone) if time.daylight else timedelta(seconds = -time.timezone)

    tzname = lambda self, dt: time.tzname[self._isdst(dt)]
    utcoffset = lambda self, dt: TZLocal.DSTOFFSET if self._isdst(dt) else TZLocal.STDOFFSET
    dst = lambda self, dt: (TZLocal.DSTOFFSET - TZLocal.STDOFFSET) if self._isdst(dt) else TZUTC.ZERO

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, dt.weekday(), 0, -1)
        return time.localtime(time.mktime(tt)).tm_isdst > 0


# These can be used whenever tzinfo objects are required in datetime functions/methods.
utc = TZUTC()   
local = TZLocal()


class TZAny(tzinfo):
    """
    Expresses any timezone, represented as [+-]HHMM
    """
    def __init__(self, tz=None):
        if tz is None:
            # Special case for unpickling (see tzinfo docs)
            self._sign = 1
            self._hours = self._mins = 0
        elif isinstance(tz, basestring):
            self._sign = -1 if tz[0] == '-' else 1
            idx = 1 if tz[0] in ('+', '-') else 0
            self._mins = int(tz[-2:])
            self._hours = int(tz[idx:len(tz)-2])
        elif isinstance(tz, (int, float)):
            self._sign = -1 if tz < 0 else 1
            self._hours = abs(tz) / 3600
            self._mins = (abs(tz) % 3600) / 60
        else:
            raise ValueError('tz must be +YYMM or number in seconds')

    def __repr__(self):
        return "<TZAny '%s'>" % self.tzname(None)

    def dst(self, dt):
        return timedelta(0)

    def tzname(self, dt):
        return '%s%02d%02d' % ('-' if self._sign < 0 else '+', self._hours, self._mins)

    def utcoffset(self, dt):
        return self._sign * timedelta(hours=self._hours, minutes=self._mins)


def from_rfc822(date):
    """
    Robust parser for an RFC822 style date.

    :param date: an RFC822 style date (e.g. `"Mon, 20 Nov 1995 19:12:08 -0500"`)
    :type date: str
    :returns: a timezone-aware datetime object
    """
    date = email.utils.parsedate_tz(date)
    if not date:
        return None

    clamp = lambda val, minval, maxval: min(max(val, minval), maxval)
    # Clamp all values in date to sane range.
    date = list(date)
    year = date[0] + 2000 if date[0] < 1900 else date[0]  # Add 2000 to year if needed
    month = clamp(date[1], 0, 12)
    day = clamp(date[2], 1, calendar.monthrange(date[0], date[1])[1])
    hour = clamp(date[3], 0, 23)
    minute = clamp(date[4], 0, 59)
    sec = clamp(date[5], 0, 59)
    tzoffset = date[-1]

    if tzoffset is None:
        # Timezone is missing.  Assume UTC.
        return datetime(year, month, day, hour, minute, sec, tzinfo=utc)
    elif abs(tzoffset) > 24*3600:
        # Timezone is +/- 24h, which is not valid.  Adjust the date with the
        # given crazy offset and treat the timezone as UTC.
        dt = datetime(year, month, day, hour, minute, sec, tzinfo=utc)
        return dt + timedelta(seconds=tzoffset)

    return datetime(year, month, day, hour, minute, sec, tzinfo=TZAny(tzoffset))


def to_timestamp(dt):
    """
    Converts a datetime object to a timestamp (seconds since epoch).

    :param dt: datetime object (naive or aware)
    :returns: timestamp (seconds since epoch)

    Native datetime objects will be treated as local time.

    .. note::
       Epoch is defined as 00:00:00 UTC on 1 January 1970.  It is *always* UTC.
    """
    if dt.tzinfo is None:
        # Treat naive objects as local time.
        return time.mktime(dt.timetuple()) + dt.microsecond / 1000000.0
    else:
        return calendar.timegm(dt.utctimetuple()) + dt.microsecond / 1000000.0


def now():
    """
    Returns the local date and time as a time-zone aware datetime object in
    local time.

    This is in contrast to the native datetime.now() which returns a naive
    object.
    """
    return datetime.now(local)


def utcnow():
    """
    Returns the current time as a time-zone aware datetime object in UTC.
    """
    return datetime.now(utc)


def today():
    """
    Returns the current day at midnight as a time-zone aware datetime object
    in local time.

    This is in contrast to the native datetime.today() which does not set
    the time to midnight and returns a naive object.
    """
    return now().replace(hour=0, minute=0, second=0, microsecond=0)
