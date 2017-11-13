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
from peewee import Using
from kalite.topic_tools.content_models import set_database, Item
import random


def content_db_init(instance):
    """
    Instance is anything we think should store the below variables, it's
    because of a strange design of the Behave test framework in which we
    cannot use conventional TestCase instances. Instead it uses the 'context'
    instance for all functions.
    
    This and the below functions are used to configure the content database
    fixture in a universal pattern.
    """
    # These are static properties because BDD tests call this class in a
    # static way (TODO: design flaw)
    instance.content_root = None
    instance.content_subtopics = []
    instance.content_subsubtopics = []
    instance.content_exercises = []
    instance.content_videos = []
    instance.content_unavailable_item = None
    instance.content_unavailable_content_path = "khan/foo/bar/unavail"
    instance.content_available_content_path = None
    instance.content_searchable_term = "Subtopic"


@set_database
def teardown_content_db(instance, db):
    """
    Seems to split out in a classmethod because BDD base_environment wants
    to reuse it.
    """
    with Using(db, [Item], with_transaction=False):
        instance.content_unavailable_item.delete_instance()
        instance.content_root.delete_instance()
        for item in (instance.content_exercises +
                     instance.content_videos +
                     instance.content_subsubtopics +
                     instance.content_subtopics):
            item.delete_instance()


@set_database
def setup_content_db(instance, db):

    # Setup the content.db (defaults to the en version)
    # Root node
    instance.content_root = Item.create(
        title="Khan Academy",
        description="",
        available=True,
        files_complete=0,
        total_files="1",
        kind="Topic",
        parent=None,
        id="khan",
        slug="khan",
        path="khan/",
        extra_fields="{}",
        youtube_id=None,
        remote_size=315846064333,
        sort_order=0
    )
    for _i in range(4):
        slug = "topic{}".format(_i)
        instance.content_subtopics.append(
            Item.create(
                title="Subtopic {}".format(_i),
                description="A subtopic",
                available=True,
                files_complete=0,
                total_files="4",
                kind="Topic",
                parent=instance.content_root,
                id=slug,
                slug=slug,
                path="khan/{}/".format(slug),
                extra_fields="{}",
                remote_size=1,
                sort_order=_i,
            )
        )
    
    # Parts of the content recommendation system currently is hard-coded
    # to look for 3rd level recommendations only and so will fail if we
    # don't have this level of lookup
    for subtopic in instance.content_subtopics:
        for _i in range(4):
            slug = "{}-{}".format(subtopic.id, _i)
            instance.content_subsubtopics.append(
                Item.create(
                    title="{} Subsubtopic {}".format(subtopic.title, _i),
                    description="A subsubtopic",
                    available=True,
                    files_complete=4,
                    total_files="4",
                    kind="Topic",
                    parent=subtopic,
                    id=slug,
                    slug=slug,
                    path="{}{}/".format(subtopic.path, slug),
                    youtube_id=None,
                    extra_fields="{}",
                    remote_size=1,
                    sort_order=_i,
                )
            )

    # We need at least 10 exercises in some of the tests to generate enough
    # data etc.
    # ...and we need at least some exercises in each sub-subtopic
    for parent in instance.content_subsubtopics:
        # Make former created exercise the prerequisite of the next one
        prerequisite = None
        for _i in range(4):
            slug = "{}-exercise-{}".format(parent.id, _i)
            extra_fields = {}
            if prerequisite:
                extra_fields['prerequisites'] = [prerequisite.id]
            new_exercise = Item.create(
                title="Exercise {} in {}".format(_i, parent.title),
                parent=parent,
                description="Solve this",
                available=True,
                kind="Exercise",
                id=slug,
                slug=slug,
                path="{}{}/".format(parent.path, slug),
                sort_order=_i,
                **extra_fields
            )
            instance.content_exercises.append(new_exercise)
            prerequisite = new_exercise
    # Add some videos, too, even though files don't exist
    for parent in instance.content_subsubtopics:
        for _i in range(4):
            slug = "{}-video-{}".format(parent.pk, _i)
            instance.content_videos.append(
                Item.create(
                    title="Video {} in {}".format(_i, parent.title),
                    parent=random.choice(instance.content_subsubtopics),
                    description="Watch this",
                    available=True,
                    kind="Video",
                    id=slug,
                    slug=slug,
                    path="{}{}/".format(parent.path, slug),
                    extra_fields={
                        "subtitle_urls": [],
                        "content_urls": {"stream": "/foo", "stream_type": "video/mp4"},
                    },
                    sort_order=_i
                )
            )

    instance.content_unavailable_item = Item.create(
        title="Unavailable item",
        description="baz",
        available=False,
        kind="Video",
        id="unavail123",
        youtube_id="unavail123",
        slug="unavail",
        path=instance.content_unavailable_content_path,
        parent=random.choice(instance.content_subsubtopics).pk,
    )
    
    instance.content_available_content_path = random.choice(instance.content_exercises).path


class KALiteTestCase(CreateDeviceMixin, TestCase):
    """The base class for KA Lite test cases."""

    def setUp(self):
        self.setUpDatabase()
        content_db_init(self)
        setup_content_db(self)
        super(KALiteTestCase, self).setUp()

    def tearDown(self):
        teardown_content_db(self)
        super(KALiteTestCase, self).tearDown()

    @classmethod
    def setUpDatabase(cls):
        """ Prepares the database for test cases. Essentially serves the same purpose as loading fixtures.
        Meant to be hijacked by the behave testing framework in "before_scenario", since behave scenarios are analogous
        to TestCases, and behave features are analogous to test suites, but due to implementation details features are
        run as TestCases. Therefore scenarios call this class method to simulate being TestCases.
        
        Seems to split out in a classmethod because BDD base_environment wants
        to reuse it.
        """
        # Do database setup stuff that's common to all test cases.
        cls.setup_fake_device()

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
        self.feature_name = kwargs.pop('feature_name')
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
        if self.feature_name:
            self.behave_config.exclude = lambda x: self.feature_name not in six.text_type(x)
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
