"""
Contains test wrappers and helper functions for
automated of KA Lite using selenium
for automated browser-based testing.
"""
import six
import sys

from selenium import webdriver

from behave.configuration import Configuration
from behave.runner import Runner as BehaveRunner
from behave.formatter.ansi_escapes import escapes

from django.core.urlresolvers import reverse
from django.test import TestCase, LiveServerTestCase

from .browser import setup_browser
from .client import KALiteClient
from .mixins.securesync_mixins import CreateDeviceMixin


class KALiteTestCase(CreateDeviceMixin, TestCase):
    """The base class for KA Lite test cases."""

    def setUp(self):
        self.setup_fake_device()

        super(KALiteTestCase, self).setUp()

    def reverse(self, *args, **kwargs):
        """Regular Django reverse function."""

        return reverse(*args, **kwargs)


class KALiteClientTestCase(KALiteTestCase):

    def setUp(self):
        self.client = KALiteClient()
        self.client.setUp()

        super(KALiteClientTestCase, self).setUp()


class KALiteBrowserTestCase(KALiteTestCase, LiveServerTestCase):
    """ This should be inherited after any mixins (like FacilityMixins)
    as the mixins may override *TestCase methods.
    """

    def setUp(self):
        self.browser = setup_browser(browser_type="Firefox")
        super(KALiteBrowserTestCase, self).setUp()

    def tearDown(self):
        self.browser.quit()

        super(KALiteBrowserTestCase, self).tearDown()

    def reverse(self, url_name, args=None, kwargs=None):
        """Given a URL name, returns the full central URL to that URL"""

        return self.live_server_url + reverse(
            url_name,
            args=args,
            kwargs=kwargs,
        )

    @property
    def is_phantomjs(self):
        return isinstance(self.browser, webdriver.PhantomJS)


# Parse options that came in.  Deal with ours, create an ARGV for Behave with
# it's options
def parse_argv(argv, option_info):
    behave_options = option_info.keys()
    new_argv = ["behave",]
    our_opts = {"browser": None}

    for index in xrange(len(argv)): #using range to have compatybility with Py3
        # If it's a behave option AND is the long version (starts with '--'),
        # then proceed to save the information.  If it's not a behave option
        # (which means it's most likely a Django test option), we ignore it.
        if argv[index] in behave_options and argv[index].startswith("--"):
            if argv[index] == "--behave_browser":
                our_opts["browser"] = argv[index + 1]
                index += 1  # Skip past browser option arg
            else:
                # Convert to Behave option
                new_argv.append("--" + argv[index][9:])

                # Add option argument if there is one
                if option_info[argv[index]] == True:
                    new_argv.append(argv[index+1])
                    index += 1  # Skip past option arg

    return (new_argv, our_opts)


# From the (unlicensed?) django-behave project
# see https://github.com/django-behave/django-behave
class DjangoBehaveTestCase(LiveServerTestCase):
    def __init__(self, **kwargs):
        self.features_dir = kwargs.pop('features_dir')
        self.option_info = kwargs.pop('option_info')
        super(DjangoBehaveTestCase, self).__init__(**kwargs)

    def get_features_dir(self):
        if isinstance(self.features_dir, six.string_types):
            return [self.features_dir]
        return self.features_dir

    def setUp(self):
        self.setupBehave()

    def setupBehave(self):
        # Create a sys.argv suitable for Behave to parse
        old_argv = sys.argv
        (sys.argv, our_opts) = parse_argv(old_argv, self.option_info)
        self.behave_config = Configuration()
        sys.argv = old_argv
        self.behave_config.browser = our_opts["browser"]

        self.behave_config.server_url = self.live_server_url  # property of LiveServerTestCase
        self.behave_config.paths = self.get_features_dir()
        self.behave_config.format = self.behave_config.format if self.behave_config.format else ['pretty']
        # disable these in case you want to add set_trace in the tests you're developing
        self.behave_config.stdout_capture =\
            self.behave_config.stdout_capture if self.behave_config.stdout_capture else False
        self.behave_config.stderr_capture =\
            self.behave_config.stderr_capture if self.behave_config.stderr_capture else False

    def runTest(self, result=None):
        # run behave on a single directory

        # from behave/__main__.py
        #stream = self.behave_config.output
        runner = BehaveRunner(self.behave_config)
        runner.test_case = self

        failed = runner.run()

        try:
            undefined_steps = runner.undefined_steps
        except AttributeError:
            undefined_steps = runner.undefined

        if self.behave_config.show_snippets and undefined_steps:
            msg = u"\nYou can implement step definitions for undefined steps with "
            msg += u"these snippets:\n\n"
            printed = set()

            if sys.version_info[0] == 3:
                string_prefix = "('"
            else:
                string_prefix = u"(u'"

            for step in set(undefined_steps):
                if step in printed:
                    continue
                printed.add(step)

                msg += u"@" + step.step_type + string_prefix + step.name + u"')\n"
                msg += u"def impl(context):\n"
                msg += u"    assert False\n\n"

            sys.stderr.write(escapes['undefined'] + msg + escapes['reset'])
            sys.stderr.flush()

        if failed:
            raise AssertionError('There were behave failures, see output above')
        # end of from behave/__main__.py
