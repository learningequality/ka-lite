"""
Default settings for Raspberry Pi
"""

from .base import *

# nginx proxy will normally be on 8008 and production port on 7007
# If ports are overridden in local_settings, run the optimizerpi script
# Currently, you need to specify kalite start --port=7007 to run KA Lite
# on a different port.

PRODUCTION_PORT = 7007
PROXY_PORT = 8008

PASSWORD_ITERATIONS_TEACHER = 2000
PASSWORD_ITERATIONS_STUDENT = 500

ENABLE_CLOCK_SET = True

DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = True

USING_RASPBERRY_PI = True
