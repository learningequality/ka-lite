"""
Test support harness to make setup.py test work.
"""
import os
import shutil

from django.conf import settings
logging = settings.LOG
from django.core.exceptions import ImproperlyConfigured
from django.db.models import get_app, get_apps
from django.core.management import call_command
from django.test.simple import DjangoTestSuiteRunner, build_suite, build_test, reorder_suite
from django.utils import unittest

from fle_utils.general import ensure_dir

from behave.configuration import options
from selenium import webdriver

from optparse import make_option

from kalite.testing.base import DjangoBehaveTestCase


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

def check_feature_file(features_dir, feature_name):
    """Used to check if a feature_name is in the specified features_dir"""
    return os.path.exists(os.path.join(features_dir, feature_name + ".feature"))


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
        # verbosity level, default 1
        self.verbosity = int(kwargs.get("verbosity"))

        # If no liveserver specified, set some default.
        #   port range is the set of open ports that Django can use to
        #   start the server.  They may have multiple servers open at once.
        if not os.environ.get('DJANGO_LIVE_TEST_SERVER_ADDRESS',""):
            os.environ['DJANGO_LIVE_TEST_SERVER_ADDRESS'] = "localhost:9000-9999"

        self._bdd_only = kwargs["bdd_only"]  # Extra options from our custom test management command are passed into
        self._no_bdd = kwargs['no_bdd']      # the constructor, but not the build_suite function where we need them.

        # Django < 1.7 serves static files using the staticfiles app, not from static root.
        # This causes django_js_reverse not to get served to the client, so we manually copy it into distributed.

        call_command("collectstatic_js_reverse", interactive=False)

        ensure_dir(os.path.join(os.path.dirname(os.path.dirname(__file__)), "distributed", "static", "django_js_reverse", "js"))
        shutil.copy2(os.path.join(settings.STATIC_ROOT, "django_js_reverse", "js", "reverse.js"),
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "distributed", "static", "django_js_reverse", "js", "reverse.js"))

        if os.environ.get("TRAVIS"):
            settings.DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = True

        return super(KALiteTestRunner, self).__init__(*args, **kwargs)

    def run_tests(self, test_labels=None, extra_tests=None, **kwargs):
        """By default, only run relevant app tests.  If you specify... you're on your own!"""

        def run_tests_wrapper_fn():
            return super(KALiteTestRunner, self).run_tests(test_labels, extra_tests, **kwargs)
        return run_tests_wrapper_fn()

    def make_bdd_test_suite(self, features_dir, feature_name=None):
        return DjangoBehaveTestCase(features_dir=features_dir, option_info=self.option_info, feature_name=feature_name)

    def build_suite(self, test_labels, extra_tests, **kwargs):
        """Run tests normally, but also run BDD tests.
        :test_labels: a tuple of test labels specified from the command line, i.e. distributed
        """
        extra_tests = extra_tests or []

        # Output Firefox version, needed to understand Selenium compatibility
        # issues
        browser = webdriver.Firefox()
        print("Successfully setup Firefox {0}".format(browser.capabilities['version']))
        browser.quit()
        # Add BDD tests to the extra_tests
        # always get all features for given apps (for convenience)
        bdd_labels = test_labels
        # if e.g. we want to run ALL the tests and so didn't specify any labels
        if not bdd_labels:
            bdd_labels = reduce(
                lambda l, x: l + [x] if 'kalite' in x else l, settings.INSTALLED_APPS, [])
            # Get rid of the leading "kalite." characters
            bdd_labels = map(lambda s: s[7:], bdd_labels)
            bdd_labels = tuple(bdd_labels)

        # if we don't want any bdd tests, empty out the bdd label list no matter what
        bdd_labels = [] if self._no_bdd else bdd_labels

        ignore_empty_test_labels = False

        for label in bdd_labels:
            feature_name = None
            if '.' in label:
                print("Found label with dot in: %s, processing individual feature" % label)
                full_label = label
                feature_name = label.split(".")[-1]
                label = label.split(".")[0]
            try:
                app = get_app(label)
            except ImproperlyConfigured as e:
                # Thrown when the app doesn't have any models
                # TODO(MCGallaspy): decide if that's reasonable behavior.
                # It means you can't put behave tests in apps with no models.
                logging.warn(e)
                continue

            # Check to see if a separate 'features' module exists,
            # parallel to the models module
            features_dir = get_features(app)
            if features_dir is not None:
                if feature_name:
                    if check_feature_file(features_dir, feature_name):
                        test_labels = filter(lambda x: x != full_label, test_labels)
                        # Flag that we should ignore test_labels if empty
                        ignore_empty_test_labels = True
                    else:
                        print("Invalid behave feature name, ignoring")
                        continue
                # build a test suite for this directory
                extra_tests.append(self.make_bdd_test_suite(features_dir, feature_name=feature_name))

        if not test_labels and ignore_empty_test_labels:
            suite = suite = unittest.TestSuite()

            if extra_tests:
                for test in extra_tests:
                    suite.addTest(test)

            suite = reorder_suite(suite, (unittest.TestCase,))
        else:
            suite = super(KALiteTestRunner, self).build_suite(test_labels, extra_tests, **kwargs)

        # remove all django module tests
        suite._tests = filter(lambda x: 'django.' not in x.__module__, suite._tests)

        if self._bdd_only:
            suite._tests = filter(lambda x: type(x).__name__ == "DjangoBehaveTestCase", suite._tests)
        return suite
