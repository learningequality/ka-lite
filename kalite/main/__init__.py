import os

import settings


########################
# PROXY SETUP
########################

if settings.HTTP_PROXY:
    os.environ['http_proxy'] = settings.HTTP_PROXY

if settings.HTTPS_PROXY:
    os.environ['https_proxy'] = settings.HTTPS_PROXY
