.. _advanced-installation:

Other options
=============

.. note::
    Every time you update kalite, you should (re)run ``kalite manage setup`` to
    ensure that the database and contents are kept updated.


.. _pip-installation:

Generic installation ``pip install``
____________________________________

You can install KA Lite from the online Python Package Index (PyPi) using its
package system `pip`.

.. note:: PyPi sources do not contain content and exercise data, so you need to
  :url-pantry:`download the contentpack en.zip manually <content/contentpacks/en.zip>` (>700 MB).

If you are installing system-wide, it's preferable to use ``ka-lite-static`` which
has dependencies bundled in and doesn't interfere with your system's setup::

    sudo pip install ka-lite-static

You can also install KA Lite in a virtual environment or on the current user's
local python packages without dependencies bundled in::

    pip install ka-lite


Portable tarballs / zip files with setup.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you can't install KA Lite on systems with the standard
Windows/Mac/Linux installers, you can fetch the KA Lite python package from
`PyPi <https://pypi.python.org/pypi/ka-lite-static>`_.

To unpack the package for installation on Linux/Mac, run:

.. parsed-literal::

   tar -xf ka-lite-static-|release|.tar.gz

Once it's unpacked, install it by entering the extracted directory and running:

.. parsed-literal::

    cd ka-lite-static-|release|
    sudo python setup.py install


.. _ppa-installation:

Debian/Ubuntu: Subscribe to updates through a PPA
_________________________________________________

We maintain a `PPA on Launchpad <https://launchpad.net/~learningequality/+archive/ubuntu/ka-lite>`_
and if you are connected to the internet, this will also give you automatic updates.

To add the PPA as a repository on an apt-based system, you need to ensure that a few libraries are present, and then add our repository and the public key that packages are signed with::


    sudo apt-get install software-properties-common python-software-properties
    sudo su -c 'echo "deb http://ppa.launchpad.net/learningequality/ka-lite/ubuntu xenial main" > /etc/apt/sources.list.d/ka-lite.list'
    sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 74F88ADB3194DD81
    sudo apt-get update
    sudo apt-get install ka-lite  # ...or 'ka-lite-raspberry-pi'


.. _gtk-installation:

User interface for Linux/GTK
____________________________

A Control Panel for simple start/stop functionality and a bit of user setup is
available with a user interface. It's not feature-complete, but good enough for simple
usage.

Make sure you have the PPA added (see :ref:`ppa-installation`), then run::

    sudo apt-get install ka-lite-gtk


On non-Debian systems, you can install the GTK interface with Pip::
  
    sudo pip install ka-lite-gtk  # Install
    ka-lite-gtk  # Launch the KA Lite UI


.. _development-installation:

Development
___________
A guide recommending how to install KA Lite for development is available in
:ref:`development-environment`.



Specific system setups
______________________


Nginx / Apache setup
~~~~~~~~~~~~~~~~~~~~

This section is written for the Django-knowledgable crowd.

KA Lite includes a web server implemented in pure Python for serving the
website, capable of handling hundreds of simultaneous users while using very
little memory. So you don't have to run Apache or Nginx for efficiency.

Apache configuration, using mod_wsgi, example would work for an Ubuntu .deb
installation: ::

    <VirtualHost *:80>
        ServerName kalite.com
        DocumentRoot /var/www/html/

        <Directory />
            Require all granted
        </Directory>

        Alias /static /var/www/.kalite/httpsrv/static
        Alias /media /var/www/.kalite/httpsrv/media
        Alias /content /var/www/.kalite/content

        WSGIScriptAlias / /usr/lib/python2.7/dist-packages/kalite/project/wsgi.py

        # Possible values include: debug, info, notice, warn, error, crit,
        # alert, emerg.
        LogLevel warn

        ErrorLog ${APACHE_LOG_DIR}/kalite-error.log
        CustomLog ${APACHE_LOG_DIR}/kalite-access.log combined
    </VirtualHost>


.. note::
    It's recommended that you install ``ka-lite-static`` in a virtualenv.
    If you are using Apache+mod_wsgi, you should copy & modify ``wsgi.py``
    to reflect the path of your venv.


If you are using uwsgi+Nginx, this is the critical part of your uwsgi
configuration, provided that you have installed kalite from PyPi or .deb: ::

    module = kalite.project.wsgi


Remember that KA Lite runs in user space and creates data files in that user's
home directory. A normal Debian/Ubuntu system has a www-data user for Apache
which is the default user for mod_wsgi and will create database files, static
files etc. for kalite in ``/var/www/.kalite/``. If you run it as another user,
it may be located somewhere else.

.. note:: Log in as the Django application server's user, e.g. www-data and
    initialize the kalite static files and database before anything you can
    run kalite with uwsgi / mod_wsgi !

Example of setting up kalite for the www-data user: ::

    sudo su -s /bin/bash www-data
    kalite manage setup
    exit

