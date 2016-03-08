.. _development-environment:

Setting up your development environment
=======================================

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

#. Run a development server and use development settings like this::
     
     kalite manage runserver --settings=kalite.project.settings.dev
  

You can also change your ``~/.kalite/settings.py`` to point to ``kalite.project.settings.dev`` by default, then you do not have to specify `--settings=...` every time you run kalite.

Now, every time you work on your development environment, just remember to switch on your virtual environment with ``workon kalite``.

.. _github: https://github.com/learningequality/ka-lite


Running directly from source
____________________________


KA Lite can also be run as a "source distribution" for development purposes.
By this, we just mean a git checkout (from `our github <https://github.com/learningequality/ka-lite/>`_).

.. note:: Running directly from source will also maintain all user data in that
          same directory! This is convenient for having several versions of
          kalite with different data on the same computer.

If you are able to use pip and install conventional python packages from an
online source, then the quickest option to install the latest stable release
of KA Lite is ``pip install ka-lite` or `pip install ka-lite-static``.


Static vs. Dynamic version
__________________________

Apart from Python itself, KA Lite depends on a couple of python applications,
mainly from the Django ecology. These applications can be installed in two ways:

* **Dynamic**: That means that they are automatically installed through
   *PIP* as a separate software package accessible to your whole system. This
   is recommended if you run KA Lite and have internet access while installing
   and updating.
* **Static**: Static means that KA Lite is installed with all the external
   applications bundled in. Use this method if you need to have KA Lite
   installed from offline media or if KA Lite's dependencies are in conflict
   with the system that you install upon.


Virtualenv
__________

You can install KA Lite in its very own separate environment that does not
interfere with other Python software on your machine like this::

    $> pip install virtualenv virtualenvwrapper
    $> mkvirtualenv my-kalite-env
    $> workon my-kalite-env
    $> pip install ka-lite
