"""
Test support harness to make setup.py test work.
"""
import functools
import os
import pdb
import sys

from django.conf import settings; logging = settings.LOG
from django.core import management
from django.db.models import get_app
from django.test.simple import DjangoTestSuiteRunner
from django.test.utils import override_settings

from behave.configuration import options

from optparse import make_option

from kalite.testing.base import KALiteBrowserTestCase, DjangoBehaveTestCase


def get_app_dir(app_module):
    app_dir = os.path.dirname(app_module.__file__)
    if os.path.basename(app_dir) == 'models':
        app_dir = os.path.abspath(os.path.join(app_dir, '..'))
    return app_dir


def get_features(app_module):
    """ Used to find feature directories for behave tests. """
    app_dir = get_app_dir(app_module)
    features_dir = os.path.abspath(os.path.join(app_dir, 'features'))
    if os.path.isdir(features_dir):
        return features_dir
    else:
        return None


def get_options():
    option_list = (
        make_option("--behave_browser",
            action="store",
            dest="browser",
            help="Specify the browser to use for testing",
        ),
    )

    option_info = {"--behave_browser": True}

    for fixed, keywords in options:
        # Look for the long version of this option
        long_option = None
        for option in fixed:
            if option.startswith("--"):
                long_option = option
                break

        # Only deal with those options that have a long version
        if long_option:
            # remove function types, as they are not compatible with optparse
            if hasattr(keywords.get('type'), '__call__'):
                del keywords['type']

            # Remove 'config_help' as that's not a valid optparse keyword
            if "config_help" in keywords:
                keywords.pop("config_help")

            name = "--behave_" + long_option[2:]

            option_list = option_list + \
                (make_option(name, **keywords),)

            # Need to store a little info about the Behave option so that we
            # can deal with it later.  'has_arg' refers to if the option has
            # an argument.  A boolean option, for example, would NOT have an
            # argument.
            action = keywords.get("action", "store")
            if action == "store" or action == "append":
                has_arg = True
            else:
                has_arg = False

            option_info.update({name: has_arg})

    return (option_list, option_info)


class KALiteTestRunner(DjangoTestSuiteRunner):
    """Forces us to start in liveserver mode, and only includes relevant apps to test"""
    (option_list, option_info) = get_options()

    def __init__(self, *args, **kwargs):
        """
        Force setting up live server test.  Adding to kwargs doesn't work, need to go to env.
        Dependent on how Django works here.
        """

        self.failfast = kwargs.get("failfast", False)  # overload
        self.verbosity = int(kwargs.get("verbosity")) # verbosity level, default 1

        # If no liveserver specified, set some default.
        #   port range is the set of open ports that Django can use to
        #   start the server.  They may have multiple servers open at once.
        if not os.environ.get('DJANGO_LIVE_TEST_SERVER_ADDRESS',""):
            os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "localhost:9000-9999"
        return super(KALiteTestRunner, self).__init__(*args, **kwargs)

    def run_tests(self, test_labels=None, extra_tests=None, **kwargs):
        """By default, only run relevant app tests.  If you specify... you're on your own!"""

        # Purge all .pyc files using the clean_pyc django extension.
        # This prevents issues when py's have been renamed or moved but
        #   the orphan pyc's are discovered and run during testing
        # pyc's are not tracked by git, so orphans can happen when an
        #   older branch has been checked out
        logging.info("Purging pyc files")
        import logging as orig_logging
        orig_logging.getLogger('django.request').setLevel('CRITICAL')
        orig_logging.getLogger('kalite').setLevel('INFO')
        management.call_command("clean_pyc", path=os.path.join(settings.PROJECT_PATH, ".."))

        orig_logging.disable(orig_logging.CRITICAL)

        @override_settings(DEBUG=settings.DEBUG or self.failfast)
        def run_tests_wrapper_fn():
            return super(KALiteTestRunner,self).run_tests(test_labels, extra_tests, **kwargs)
        return run_tests_wrapper_fn()

    def make_bdd_test_suite(self, features_dir):
        return DjangoBehaveTestCase(features_dir=features_dir, option_info=self.option_info)

    def build_suite(self, test_labels, extra_tests, **kwargs):
        """Run tests normally, but also run BDD tests.
        """
        extra_tests = extra_tests or []

        # Add BDD tests to the extra_tests
        # always get all features for given apps (for convenience)
        for label in test_labels:
            if '.' in label:
                print("Ignoring label with dot in: %s" % label)
                continue
            app = get_app(label)

            # Check to see if a separate 'features' module exists,
            # parallel to the models module
            features_dir = get_features(app)
            if features_dir is not None:
                # build a test suite for this directory
                extra_tests.append(self.make_bdd_test_suite(features_dir))

        return super(KALiteTestRunner, self).build_suite(test_labels, extra_tests, **kwargs)
