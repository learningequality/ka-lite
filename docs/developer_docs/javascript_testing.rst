Purpose and creation of Javascript Unit Tests in KA Lite
========================================================

Purpose
-------

Our Backbone Models and Views can end up having a lot of methods. It is important that all of those methods observe the correct input output characteristics. Hence it is important that we write tests that guarantee that our methods either take the correct input and produce the right output, or, as is often the case, produce the right side effects on models, views, or the DOM.

In pursuit of this lofty goal of having every method and object testable and tested, there will be some requirements of refactoring along the way. Some of the code that has already been written for the KA Lite project is not conveniently parcelled in such a way as to be conducive to testing individual components in an atomic fashion. In order to ensure that functionality does not break as a result, we have integration tests (which are currently only implemented using Selenium scripted by Python) - for now we are avoiding writing such integration tests in Javascript as well so as to avoid duplication.

Setting up your Test Environment
--------------------------------

#. Install requirements:
    * `install node <http://nodejs.org/download/>`_ if you don't have it already.
    * `install pip <https://pypi.python.org/pypi/pip>`_ if you don't have it already.

#. Install the dependencies listed in requirements.txt: ``pip install -r requirements.txt``

#. Install the dependencies listed in packages.json: ``sudo npm install``

Getting Your Javascript to be Testable in KA Lite
-------------------------------------------------

Before you can test your javascript, it must be capable of being bundled in such a way that django-compress (the asset compression package we use) is able to write it to a Javascript file which can then be loaded by the Javascript test runner, karma.

In order to make this happen, use compression tags around blocks of Javascript script imports inside django templates for example, from learn.html::

    {% compress js file learnjs %}
    <!--[if !IE]> -->
    <script src="{% static "video-js/video.js" %}"></script>
    <script src="{% static "video-js/video-speed.js" %}"></script>
    <script>
        _V_.options.flash.swf = window.flash_swf;
    </script>
    <!-- <![endif]-->
    <script src="{% static "soundmanager/soundmanager2-nodebug-jsmin.js" %}"></script>

    <script src="{% static 'js/distributed/content/models.js' %}"></script>
    <script src="{% static 'js/distributed/content/views.js' %}"></script>

    <script src="{% static 'js/distributed/video/models.js' %}"></script>
    <script src="{% static 'js/distributed/video/views.js' %}"></script>

    <script src="{% static 'js/distributed/audio/views.js' %}"></script>

    <script src="{% static 'js/jquery.slimscroll.min.js' %}"></script>
    <script src="{% static 'js/distributed/topics/models.js' %}"></script>
    <script src="{% static 'js/distributed/topics/views.js' %}"></script>
    <script src="{% static 'js/distributed/topics/router.js' %}"></script>

    {% endcompress %}

You will also need to inclue the tag ``{% load compress %}`` at the top of a template in order to make use of the ``compress`` template tag.

Let's examine the important details of ``{% compress js file learnjs %}`` - the ``compress`` tag name is followed by the kind of file being compressed (``js``), then two optional parameters. The first tells django-compress to compress the assets to a separate file (rather than rendering the concatenated Javascript inline in the HTML), the second gives a name to the code block. This should be a unique name across the entire code base. At current there is no way to know what names have already been used, except by examining karma.conf.js in the root of the project.

The name of the block is important for making it available for Javascript testing - it needs to be manually added to the karma.conf.js here::

    // list of files / patterns to load in the browser
    files: [
      file_map['basejs'].slice(1),
      file_map['perseusjs_1'].slice(1),
      file_map['perseusjs_2'].slice(1),
      file_map['learnjs'].slice(1),
      file_map['pdfjs'].slice(1),
      // INSERT NEW JAVASCRIPT BUNDLES HERE
      '**/tests/javascript_unit_tests/*.js',
      'testing/testrunner.js'
    ],

So if you had created a new compression block called 'exparrotshop' then you would add the element ``file_map['exparrotshop'].slice(1)`` to the array.

Writing a Test
--------------

You are now ready to write a test. All Javascript unit tests live inside the appropriate app. For example, if you were writing a unit test for Javascript code for the coachreport app, you would put your test file in kalite/coachreports/tests/javascript_unit_tests/. Call your file the name of the Model, View, or Router you are testing, or use an existing test file if you are extending an already tested Model or View.
For example, the Session Model test file is called::

    session_model_test.js

Each test file should start with a definition statement::

    module("Session Model Tests", {
      setup: function() {
        return this.sessionModel = new SessionModel();
      }
    });

The text gives the name of the suite of tests you will be writing in this file. The ``setup`` method defines something that happens prior to every single test being run. ``this`` gets returned to every subsequent test as ``this`` also, so anything set as an attribute of ``this`` will be available inside each test.

After the module definition, you can define any number of tests. Here is a simple example::

    test("Default values", function() {
      expect(2);

      equal(this.sessionModel.get("SEARCH_TOPICS_URL"), "");
      equal(this.sessionModel.get("STATUS_URL"), "");
    });

This simple test is checking the default values for the Session Model defined during the setup method above. At the beginning of the test, we declare how many assertion statements will be made during the course of the test. Not specifying this number correctly will cause a failure. The tests are written in `QUnit <https://qunitjs.com/>`_ whose docs can be referred to for a complete set of assertions.

Running Tests
-------------

When you have written your tests, before you can run them, we need to bundle the Javascript for testing. In order to do this, from the root of the project run::

    bin/kalite manage bundleassets

This will bundle all the django-compress tags and make concatenated files. It will also update the file_map that our Karma config uses to find these files. When this is complete, simply run::

    karma start

This will run through all the Javascript tests and report on failures. N.B. Karma is often, and most helpfully, run in continuous integration mode - our code base does not currently suppor that, but hopefully will in the future.
