from datetime import datetime

try:
    # Django 1.4+
    from django.utils import timezone
except:
    timezone = None

try:
    # Django 1.4+
    from django.utils import formats
except:
    from django.utils.translation import get_date_formats
    from django.utils import dateformat
    formats = None

def now():
    """
    Returns a time-zone aware, UTC ``datetime``, if necessary, otherwise just a
    simple "naive" ``datetime`` object of the current date and time.
    """
    if timezone:
        return timezone.now()
    return datetime.now()

def get_tz_date(dt, meth, tz):
    if timezone:
        tz = tz.lower()
        if tz == 'utc':
            dt = meth(dt, timezone.utc)
        elif tz == 'default':
            dt = meth(dt, timezone.get_default_timezone())
        elif tz == 'current':
            dt = meth(dt, timezone.get_current_timezone())
    return dt

def make_naive(dt, tz='utc'):
    if timezone:
        dt = get_tz_date(dt, timezone.make_naive, tz)
    return dt

def make_aware(dt, tz='utc'):
    if timezone:
        dt = get_tz_date(dt, timezone.make_aware, tz)
    return dt

def local_dateformat(dt):
    """
    Returns a string representation of the given ``datetime`` ``dt``.
    """
    if formats:
        try:
            return formats.localize(dt, use_l10n=True)
        except TypeError:
            # Django 1.2
            return formats.localize(dt)
    return dateformat.format(dt, get_date_formats()[1])


def localtime(dt):
    if timezone:
        return timezone.localtime(dt)
    return dt