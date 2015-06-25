"""
Override the built-in test command, in order to define custom options.
In particular, we'd like to be able to run only behave tests.
"""
from optparse import make_option

try:
    from south.management.commands.test import Command as TestCommand
except ImportError:
    from django.core.management.commands.test import Command as TestCommand

class Command(TestCommand):
    """
    We just want to add an extra option to the builtin test command.
    This class doesn't handle the extra logic of that option; instead it's in our test runner.
    See kalite.testing.testrunner
    """
    option_list = TestCommand.option_list + (
        make_option(
            '--bdd-only',
            action='store_true',
            dest='bdd_only',
            default=False,
            help="Only run the behave tests."
        ),
        make_option(
            '--no-bdd',
            action='store_true',
            dest='no_bdd',
            default=False,
            help="Don't run the behave tests."
        )
    )
