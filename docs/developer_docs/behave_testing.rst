Behavior-Driven Integration Tests
=================================

Part of our comprehensive testing intiative is to write better integration tests.
The goals are to:

1. Stop using browser driven integration tests as unit tests. (Such slow...)
2. Have robust integration tests that don't fail randomly.
3. Use behavior-driven tests to clarify design goals of features.

We're using `behave 1.2.4 <http://pythonhosted.org/behave/>`_ to run our integration tests.
Behavior driven tests are specified using the Gherkin specification language, and then behave builds a test suite from step implementations that are directly mapped to clauses from the Gherkin specification.

Running the integration tests
-----------------------------

To get the dependencies run ```pip install -r dev_requirements.txt```. This should install the correct version of behave. Selenium is also required but is currently included in our python-packages directory.

To run the tests simply run ```bin/kalite manage test``` just like you used to. This will automatically search out tests using both the unit test framework and the behave framework. You can specify apps, but right now there's no way to just run integration tests.

Running a specific test
^^^^^^^^^^^^^^^^^^^^^^^

If you want to run for instance the set of tests in ``kalite/distributed/features/content_rating.feature``, use this command, applying the app label ``distributed`` and the name of the feature ``content_rating``::

    bin/kalite manage test distributed.content_rating --bdd-only


Anatomy of the integration tests
--------------------------------

The test command will look inside each app for a ```features``` directory. Inside that directory should be one or more ```[name].feature``` files written in the Gherkin specification language. See `the behave docs <http://pythonhosted.org/behave/tutorial.html#feature-files>`_ for more details on Gherkin, or look in the ```control_panel``` app, where your humble author has attempted to provide some examples.

The test runner will parse the ```.feature``` files and attempt to build a test suite from step specifications found in any python files (the name is irrelevant) in the ```steps``` subdirectory. There is a 1-to-1 mapping between the clauses you write in the Gherkin specification and the steps you implement, so it can save you time to reuse clauses. Steps can also be `templated <http://pythonhosted.org/behave/api.html#step-parameters>`_ to match clauses that follow a pattern.

You can also set up the test environment at key stages in the testing process by writing hooks in an ```environment.py``` file in the ```features``` directory. In the ```control_panel``` example, the ```before_feature``` function is defined to log the testing user in as an admin before each feature tagged with the ```@as_admin``` tag in the specification. In ```testing/base_environment.py```, the ```before_all``` and ```after_all``` hooks are defined to set up a Selenium WebDriver instance on the context object that is passed around by the test runner. This file is intended to be used as a base for all the integration tests, so if there is some setup common to all integration tests then put it there. You can then import those functions in the ```environment.py``` of specific apps, and extend or overwrite as necessary.

Finally, in ```testing/behave_helpers.py``` you'll find various functions that should be generally useful for all integration tests. If you find yourself wishing you had a nice useful function, add it here. In order to avoid reproducing functionality while we phase out the old integration tests, if some functionality already exists in the form of a mixin, you should import it into that file and wrap it in a new function. Be very reticent about importing mixin code! A good rule of thumb is to glance at how something is implemented in the mixins first, and only import it if it's not trivial to reproduce. Only re-write if there's *no* chance of the new code producing an error! The main goal is to avoid maintaining two sets of code.

Suggested workflow for writing new features
-------------------------------------------

Ideally you should:

1. Specify your integration tests.
2. Write failing steps.
3. Write code that makes your tests pass.

In practice, at least try to specify the tests first. Then you can seek out assistance implementing the steps.

Selenium gotchas (aka race conditions)
--------------------------------------

Finding elements on the page can be subject to race conditions if the page is not yet completely loaded, or if the DOM changes in response to AJAX stuff. Selenium pprovides methods for finding elements with and without explicit waits. When in doubt, use a wait. If your app is AJAX-y, write testable code by putting in events or flags that Selenium can explicitly wait for. The Selenium ```get``` method of browsing will wait for the page to fully load. *Do not assume* that following links using e.g. the ```click``` method will wait for the page to load -- *it does not*. To summarize:

1. Incorporate explicit flags in your code that Selenium can use in waits.
2. Don't use unsafe methods that don't wait unless you're 100% certain there's no possibility for a race condition.
