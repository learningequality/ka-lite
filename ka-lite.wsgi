import os
import sys

# sys.path = ['/home/jamalex/webapps/ka-lite', '/home/jamalex/webapps/ka-lite/lib/python2.5'] + sys.path

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'kalite.settings'
application = WSGIHandler()
