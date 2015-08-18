Advanced topics
===============

.. _advanced-installation:

Source code / development
_________________________

KA Lite can also be run as a "source distribution" for development purposes.
By this, we just mean a git checkout (from `our github <https://github.com/learningequality/ka-lite/>`_).

.. note:: Running directly from source will also maintain all user data in that
          same directory! This is convenient for having several versions of
          kalite with different data on the same computer.

If you are able to use pip and install conventional python packages from an
online source, then the quickest option to install the latest stable release
of KA Lite is `pip install ka-lite` or `pip install ka-lite-static`.


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


Installing through PIP or with setup.py
_______________________________________

This documentation is preliminary and will be moved and restructured.

For command line users with access to PIP, you can install the following versions of KA Lite::

    $> pip install ka-lite


Static version
______________

If you need to run KA Lite with static dependencies bundled and isolated from
the rest of your environment, you can run::

    $> pip install ka-lite-static


Portable tarballs / zip files with setup.py
___________________________________________

You can also fetch a tarball directly from `PyPi <https://pypi.python.org/pypi/ka-lite-static>`.
Do this for the sake of carrying KA Lite on an offline media. You can then
unpack the tarball and run ``python setup.py install``.


Developer setup
_______________

Developers should consider installing in "editable" mode. That means, create a
git clone and from the git cloned directory, run::

    $> git clone git@github.com:learningequality/ka-lite.git
    $> cd ka-lite
    $> # You may wish to create and activate a virtual env here
    $> pip install -e .


Testing installers
__________________

Here's an overview of the various ways of installing KA Lite as a reference
to testers and package maintainers:

 * Source code setuptools test: ``python setup.py install``
 * Source code setuptools test, static: ``python setup.py install --static``
 * Source code pip test: ``pip install .``
 * Source code pip test, static: N/A, the ``--static`` option can't be passed through pip.
 * Dynamic tarball testing: ``python setup.py sdist --static`` + ``pip install dist/ka-lite-XXXX.tar.gz``.
   * Removal: ``pip remove ka-lite``.
 * Static tarball testing: ``python setup.py sdist --static`` + ``pip install dist/ka-lite-static-XXXX.tar.gz``
   * Removal: ``pip remove ka-lite-static``.
 * Wheel / whl: Not supported in 0.14.

Those testing scenarios should be sufficient, but there may be small differences
encountered that we need to look at once in a while with
``pip install -e`` (editable mode) or unzipping a source "ka-lite.XXX.zip" and
run setup.py with setuptools instead of through pip.

Using ``pip install`` and ``--static``: Is not possible, so you cannot install
the static version in "editable" mode. This is because pip commands do not
pass our user-defined options to setup.py.


Nginx / Apache setup
====================

This section is written for the Django-knowledgable crowd.

KA Lite includes a web server implemented in pure Python for serving the
website, capable of handling hundreds of simultaneous users while using very
little memory. So you don't have to run Apache or Nginx for efficiency.

Apache configuration, using mod_wsgi, example would work for an Ubuntu .deb
installation: ::

    <VirtualHost *:80>
        ServerName kalite.com
        DocumentRoot /var/www/html/

        Alias /static /var/www/.kalite/static
        Alias /media /var/www/.kalite/media

        WSGIScriptAlias / /usr/lib/python2.7/dist-packages/kalite/project/wsgi.py

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        ErrorLog ${APACHE_LOG_DIR}/kalite-error.log
        CustomLog ${APACHE_LOG_DIR}/kalite-access.log combined
    </VirtualHost>


If you are using uwsgi+Nginx, this is the critical part of your uwsgi
configuration, provided that you have installed kalite from PyPi or .deb: ::

    module = kalite.project.wsgi


Remember that kalite runs in user space and creates data files in that user's
home directory. A normal Debian/Ubuntu system has a www-data user for Apache
which is the default user for mod_wsgi and will create database files, static
files etc. for kalite in ``/var/www/.kalite/``. If you run it as another user,
it may be located somewhere else.


.. note:: Log in as the Django application server's user, e.g. www-data and
    initialize the kalite static files and database before anything you can
    run kalite with uwsgi / mod_wsgi !

Example of setting up kalite for the www-data user: ::

    $> sudo su -s /bin/bash www-data
    $> kalite manage setup
    $> exit
