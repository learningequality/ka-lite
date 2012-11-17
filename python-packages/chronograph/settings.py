from django.conf import settings

# Number of seconds that a lock file must be "stale" for a Job to be considered
# "dead".  Default is 1 minute (60 seconds)
LOCK_TIMEOUT = getattr(settings, 'CHRONOGRAPH_LOCK_TIMEOUT', 60)