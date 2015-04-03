import requests
from kalite.version import *

# Modify Request's default user agent to include the KA Lite version number
# (this is done in this file because putting it in __init__.py causes circular imports,
# and putting it in urls.py doesn't get loaded by management commands)
base_headers = requests.defaults.defaults["base_headers"]
base_headers["User-Agent"] = ("ka-lite/%s " % VERSION) + base_headers["User-Agent"]
