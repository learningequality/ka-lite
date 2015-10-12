"""
WSGI config for kalite.project

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

# Because we still use an old django version
from django.core.handlers.wsgi import WSGIHandler

# Add ka-lite to the path
PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
sys.path = [
    PROJECT_PATH,
    os.path.join(PROJECT_PATH, "../../"),
    os.path.join(PROJECT_PATH, "../../python-packages/"),
    os.path.join(PROJECT_PATH, "../../dist-packages/"),
] + sys.path

# We set the variable directly because of how mod_wsgi uses a thread pool
# with shared ENVs which will break when running on multiple django vhosts.
os.environ['DJANGO_SETTINGS_MODULE'] = 'kalite.project.settings.default'
application = WSGIHandler()

# Django 1.8:
# from django.core.wsgi import get_wsgi_application
#
# os.environ.setdefault('DJANGO_SETTINGS_MODULE',
#                      'kalite.project.settings.production')
# application = get_wsgi_application()
