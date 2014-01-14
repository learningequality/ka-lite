import settings


########################
# PROXY SETUP
########################

if settings.HTTP_PROXY:
    os.environ['http_proxy'] = settings.HTTP_PROXY
