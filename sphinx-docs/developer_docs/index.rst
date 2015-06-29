Setting up your development environment
=======================================

KA Lite is like a normal django project, if you have done Django before, you will recognize most of these steps.

  1. Check out the project from our _`github`
  1. Create a virtual environment "kalite" that you will work in:
     .. ::
       sudo pip install virtualenvwrapper
       mkvirtualenv kalite
       workon kalite
  1. Install kalite in your virtualenv in "editable" mode, meaning that the source is just linked:
     .. ::
       cd path/to/repo
       pip install -e .
  1. Install additional development tools:
     .. ::
       pip install -r requirements_dev.txt
  1. Run a development server and use development settings like this:
     .. ::
       kalite manage runserver --settings=kalite.project.settings.dev
  

You can also change your ``~/.kalite/settings.py`` to point to ``kalite.project.settings.dev`` by default, then you do not have to specify `--settings=...` every time you run kalite.

Now, everytime you work on your development environment, just remember to switch on your virtual environment with `workon kalite`.

.. _github: https://github.com/learningequality/ka-lite


Developer Docs
==============

Useful stuff our devs think that the rest of our devs ought to know about.

.. toctree::
    Developing Front End Code <front_end_code>
    Javascript Unit Tests <javascript_testing>
    Behavior-Driven Integration Tests <behave_testing>
    Profiling KA Lite <profiling>
    Developer Utility Commands <utility>
    Logging <logging>
