"""
Default settings for Raspberry Pi
"""

from .base import *

# nginx proxy will normally be on 8008 and production port on 7007
# You need to specify kalite start --port=7007 to run KA Lite
# on a different port. This is done by default in the debian package's
# init.d script, where this settings module is also used.
#
# See: https://learningequality.org/ka-lite/ for installation sources

USER_FACING_PORT = 8008

PASSWORD_ITERATIONS_TEACHER = 2000
PASSWORD_ITERATIONS_STUDENT = 500

# This no-op option is used for a couple of views that have user information
# specifically targeted the RPi users.
USING_RASPBERRY_PI = True

