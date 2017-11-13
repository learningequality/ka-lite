.. _development-environment:

Getting started
===============

.. warning::  These directions may be out of date! This page needs to be consolidated with the `Getting Started page on our wiki <https://github.com/learningequality/ka-lite/wiki/Getting-started>`_.

Recommended setup
_________________


KA Lite is like a normal django project, if you have done Django before, you will recognize most of these steps.

#. Check out the project from our `github`_
#. Create a virtual environment "kalite" that you will work in::
     
     sudo pip install virtualenvwrapper
     mkvirtualenv kalite
     workon kalite

#. Install kalite in your virtualenv in "editable" mode, meaning that the source is just linked::
     
     cd path/to/repo
     pip install -e .

#. Install additional development tools::
     
     pip install -r requirements_dev.txt

#. Build static assets such as javascript::
     
     make assets

#. Run the setup, which will bootstrap the database::
     
     kalite manage setup

#. Run a development server and use development settings like this::
     
     kalite manage runserver --settings=kalite.project.settings.dev
  

You can also change your ``~/.kalite/settings.py`` to point to ``kalite.project.settings.dev`` by default, then you do not have to specify `--settings=...` every time you run kalite.

Now, every time you work on your development environment, just remember to switch on your virtual environment with ``workon kalite``.

.. _github: https://github.com/learningequality/ka-lite


Static vs. Dynamic version
__________________________

Apart from Python itself, KA Lite depends on a couple of python applications,
mainly from the Django ecosystem. These dependencies can be installed in two ways:

* **Dynamic**: Means dependencies are automatically installed through
  *PIP* as a separate software package accessible to your whole system. This
  is recommended if you run KA Lite and have internet access while installing
  and updating.
* **Static**: Static means that KA Lite is installed with all the external
  dependencies bundled in. Use this method if you need to have KA Lite
  installed from offline media or if KA Lite's dependencies are in conflict
  with the system that you install upon.


Virtualenv
__________

You can install KA Lite in its very own separate environment that does not
interfere with other Python software on your machine like this::

    pip install virtualenv virtualenvwrapper
    mkvirtualenv my-kalite-env
    workon my-kalite-env
    pip install ka-lite


Running tests
_____________


On Circle CI, we run Selenium 2.53.6 because it works in their environment. However,
for more recent versions of Firefox, you need to upgrade Selenium::

    pip install selenium\<3.5 --upgrade

To run all of the tests (this is slow)::

    kalite manage test

To skip BDD tests (because they are slow)::

    kalite manage test --no-bdd

To run a specific test (not a BDD test), add an argument ``<app>.<TestClass>``::

    kalite manage test updates.TestDownload --no-bdd

To run a specific item from :ref:`bdd`, use ``<app>.<feature_module_name>``::

    kalite manage test distributed.content_rating --bdd-only

