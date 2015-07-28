Contributing to KA Lite
============================

Want to contribute? You can check us out on `github <https://github.com/learningequality/ka-lite/>`_, or browse the link(s) below.


Setting up your development environment
---------------------------------------

KA Lite is like a normal django project, if you have done Django before, you will recognize most of these steps.

#. Check out the project from our _`github`
#. Create a virtual environment "kalite" that you will work in::

     sudo pip install virtualenvwrapper
     mkvirtualenv kalite
     workon kalite

#. Install kalite in your virtualenv in "editable" mode, meaning that the source is just linked::

     cd path/to/repo
     pip install -e .

#. Install additional development tools::

     pip install -r requirements_dev.txt

#. Run a development server and use development settings like this::

     kalite manage runserver --settings=kalite.project.settings.dev


You can also change your ``~/.kalite/settings.py`` to point to ``kalite.project.settings.dev`` by default, then you do not have to specify `--settings=...` every time you run kalite.

Now, every time you work on your development environment, just remember to switch on your virtual environment with ``workon kalite``.

.. _github: https://github.com/learningequality/ka-lite


If you wish to view output from the server, you have a few options:

*  Start the server using the command ``kalite manage runserver`` (this doesn't start the job scheduler).
*  Start the server with ``kalite start --foreground``. This will start the server using CherryPy and a single thread, with output going to your terminal.
*  Run the normal mode ``kalite start``, and check ``~/.kalite/server.log`` for output.



Special Topics
--------------------------
.. toctree::

    Front End Code <front_end_code>
    Documentation <documentation>
    Javascript Unit Tests <javascript_testing>
    Behavior-Driven Integration Tests <behave_testing>
    Developer Utility Commands <utility>
