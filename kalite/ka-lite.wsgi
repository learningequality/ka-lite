import os, sys, warnings

warnings.filterwarnings('ignore', message=r'Module .*? is being added to sys\.path', append=True)

PROJECT_PATH = os.path.dirname(os.path.realpath(__file__))

sys.path = [
    os.path.join(PROJECT_PATH, "../"),
    os.path.join(PROJECT_PATH, "../python-packages/"),
] + sys.path


# After setting up paths, we're ready to proceed with Django config.

from django.core.handlers.wsgi import WSGIHandler

os.environ['DJANGO_SETTINGS_MODULE'] = 'kalite.settings'
application = WSGIHandler()
