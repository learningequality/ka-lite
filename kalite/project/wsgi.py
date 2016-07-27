"""
WSGI config for kalite.project

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import sys

# Enable this if you're using Apache + mod_wsgi and have KA Lite installed in a
# virtualenv
# activate_this = os.path.join(
#     "/home/user/.virtualenvs/kalite",
#     "bin/activate_this.py"
# )
# execfile(activate_this, dict(__file__=activate_this))

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))
KALITE_INSTALL_PATH = os.path.dirname(os.path.dirname(PROJECT_PATH))

sys.path = [
    PROJECT_PATH,
    KALITE_INSTALL_PATH,
] + sys.path

# Add python-packages and dist-packages to the path
from kalite import ROOT_DATA_PATH

if os.path.exists(os.path.join(ROOT_DATA_PATH, 'python-packages')):
    sys.path = [
        os.path.join(ROOT_DATA_PATH, "python-packages"),
        os.path.join(ROOT_DATA_PATH, "dist-packages"),
    ] + sys.path
else:
    sys.path = [
        os.path.join(KALITE_INSTALL_PATH, "python-packages"),
        os.path.join(KALITE_INSTALL_PATH, "dist-packages"),
    ] + sys.path

os.environ.setdefault(
    "KALITE_HOME",
    os.path.join(os.path.expanduser("~"), ".kalite")
)

# Because we still use an old django version
from django.core.handlers.wsgi import WSGIHandler

# Where to store user data
KALITE_HOME = os.environ["KALITE_HOME"]

if not os.path.isdir(KALITE_HOME):
    try:
        os.mkdir(KALITE_HOME)
    except OSError:
        raise RuntimeError(
            "Could not create {} -- please create it manually".format(
                KALITE_HOME
            )
        )

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
