import fnmatch
import os
import sys
import warnings
from datetime import datetime
from threading import Thread
from time import sleep, time
from optparse import make_option

from django.conf import settings; logging = settings.LOG
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.utils.importlib import import_module
from django.utils._os import upath

KA_LITE_PATH = os.path.abspath(os.path.join(settings.PROJECT_PATH, ".."))


def make_path_relative(path):
    if path.startswith(KA_LITE_PATH):
        path = path[len(KA_LITE_PATH)+1:]
    return path


def get_app_subdirectory_paths(subdir):
    paths = []
    for appname in settings.INSTALLED_APPS:
        app = import_module(appname)
        subdirpath = os.path.join(os.path.dirname(upath(app.__file__)), subdir)
        if os.path.exists(subdirpath):
            # paths.append(make_path_relative(subdirpath))
            paths.append(subdirpath)
    return paths


def get_paths_matching_pattern(pattern, starting_directory=KA_LITE_PATH):
    paths = []
    for root, dirs, files in os.walk(KA_LITE_PATH):
        # root = make_path_relative(root)
        paths += [os.path.join(root, d) for d in dirs if fnmatch.fnmatch(d, pattern)]
        paths += [os.path.join(root, f) for f in files if fnmatch.fnmatch(f, pattern)]
    return paths


def get_paths_ending_with(substring, starting_directory=KA_LITE_PATH):
    paths = []
    for root, dirs, files in os.walk(KA_LITE_PATH):
        # root = make_path_relative(root)
        paths += [os.path.join(root, d) for d in dirs if os.path.join(root, d).endswith(substring)]
        paths += [os.path.join(root, f) for f in files if os.path.join(root, f).endswith(substring)]
    return paths


def get_blacklist(removeunused=False, exclude_patterns=[], removestatic=False, removetests=False, removei18n=False, removekhan=False, **kwargs):

    blacklist = []

    if removeunused:
        blacklist += get_paths_ending_with("perseus/src")
        blacklist += get_paths_matching_pattern(".git")
        blacklist += get_paths_matching_pattern(".gitignore")
        blacklist += get_paths_matching_pattern("requirements.txt")
        blacklist += [
            "python-packages/postmark"
            "python-packages/fle_utils/feeds",
            "python-packages/announcements",
            "python-packages/tastypie/templates",
            "python-packages/tastypie/management",
            "python-packages/django/contrib/admindocs",
            "python-packages/django/contrib/flatpages",
            # "python-packages/django/contrib/sitemaps",
            "python-packages/django/contrib/comments",
        ]
        # don't need i18n stuff for django admin, since nobody should be seeing it
        blacklist += get_paths_matching_pattern("locale", starting_directory=os.path.join(KA_LITE_PATH, "python-packages/django"))

    for pattern in exclude_patterns:
        blacklist += get_paths_matching_pattern(pattern)

    if removestatic:
        blacklist += get_app_subdirectory_paths("static")

    if removetests:
        blacklist += get_app_subdirectory_paths("tests")
        # blacklist += get_app_subdirectory_paths("tests.py")
        blacklist += get_paths_matching_pattern("__tests__")
        blacklist += [
            "kalite/static/khan-exercises/test",
            "python-packages/selenium",
            "kalite/testing",
        ]

    if removei18n:
        blacklist += get_paths_matching_pattern("locale")
        blacklist += get_paths_matching_pattern("localeplanet")
        blacklist += get_paths_matching_pattern("*.po")
        blacklist += get_paths_matching_pattern("*.mo")
        blacklist += get_paths_ending_with("jquery-ui/i18n")

    if removekhan:
        blacklist += get_paths_matching_pattern("khan-exercises")
        blacklist += get_paths_matching_pattern("perseus")

    # I want my paths absolute
    blacklist = [os.path.abspath(os.path.join("..", path)) for path in blacklist]
    return blacklist


class Command(BaseCommand):
    args = ""
    help = "Outputs a blacklist of files not to include when distributing for production."

    option_list = BaseCommand.option_list + (
        make_option('', '--removeunused',
            action='store_true',
            dest='removeunused',
            default=False,
            help='Exclude a number of files not currently being used at all'),
        make_option('-e', '--exclude',
            action='append',
            dest='exclude_patterns',
            default=[],
            help='Exclude files matching a pattern (e.g. with a certain extension). Can be repeated to include multiple patterns.'),
        make_option('', '--removestatic',
            action='store_true',
            dest='removestatic',
            default=False,
            help='Exclude static files in INSTALLED_APPS (be sure to run collectstatic)'),
        make_option('', '--removetests',
            action='store_true',
            dest='removetests',
            default=False,
            help='Exclude tests folders in INSTALLED_APPS'),
        make_option('', '--removei18n',
            action='store_true',
            dest='removei18n',
            default=False,
            help='Exclude locale and other i18n files/folders'),
        make_option('', '--removekhan',
            action='store_true',
            dest='removekhan',
            default=False,
            help='Exclude khan-exercises, perseus, and other KA-specific stuff'),
    )

    def handle( self, *args, **options ):

        print "\n".join(get_blacklist(**options))

        # python -O /usr/lib/python2.6/compileall.py .
