.. _advanced-installation:

Advanced installation options
=============================

.. note::
    Every time you install or update kalite, you should (re)run ``kalite manage setup``
    to setup the database and download assessment items (video descriptions,
    exercises etc.).


.. _ppa-installation:

Debian/Ubuntu: Subscribe to updates through a PPA
_________________________________________________

We maintain a `PPA on Launchpad <https://launchpad.net/~learningequality/+archive/ubuntu/ka-lite>`_
and if you are connected to the internet, this will also give you automatic updates::

    sudo apt-get install software-properties-common python-software-properties
    sudo add-apt-repository ppa:learningequality/ka-lite
    sudo apt-get update
    sudo apt-get install ka-lite


.. _gtk-installation:

User interface for Debian/Ubuntu
__________________________________

Make sure you have the PPA added, then run::

    sudo apt-get install ka-lite-gtk


.. _development-installation:

Development
___________
A guide recommending how to install KA Lite for development is available in
:ref:`development-environment`.



.. _pip-installation:

Generic installation (pip install)
__________________________________


Installing through pip or with setup.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For command line users with access to pip, you can install KA Lite from an
online source like this::

    $> pip install ka-lite


Static version
~~~~~~~~~~~~~~

If you need to run KA Lite with static dependencies bundled and isolated from
the rest of your environment, you can run::

    $> pip install ka-lite-static


Portable tarballs / zip files with setup.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you can't install KA Lite on systems with the standard Windows/Mac/Linux installers,
you can fetch the KA Lite python package from `PyPi <https://pypi.python.org/pypi/ka-lite-static>`_.

To unpack the package for installation, run:

.. parsed-literal::

   $> tar -xf ka-lite-static-|release|.tar.gz

Once it's unpacked, install it by entering the extracted directory and running::

    $> sudo python setup.py install.

Beware that the PyPi sources do not contain assessment items, so you need to
:url-pantry:`download the contentpack en.zip manually <content/contentpacks/en.zip>` (>700 MB)..


Specific system setups
______________________

.. _raspberry-pi-wifi:

Raspberry Pi Wi-Fi
~~~~~~~~~~~~~~~~~~

.. note:: Two Wi-Fi USB modules have been tested with KA Lite on the Raspberry Pi

    * Raspberry Pi WiPi adaptor
    * Edimax EW-7811Un

In our tests, we found that the WiPi adaptor supported a higher number tablet connections.


.. note:: The Raspberry Pi may crash if the USB adaptor is inserted or removed while the computer is switched on.

    * Make sure to shutdown and remove the power from the Raspberry Pi.
    * Afterwards, insert the wireless USB adaptor.
    * Lastly, switch the Raspberry Pi on.

#. Install the .deb package, see :ref:`raspberry-pi-install`.
#. Get the network configuration scripts.
    * ``cd /opt``
    * ``sudo git clone https://github.com/learningequality/ka-lite-pi-scripts.git``
#. Install and configure the access point::
  
    cd /opt/ka-lite-pi-scripts
    sudo ./configure.sh

   .. note::
         If using the Edimax EW-7811UN, ignore the "hostapdSegmentation fault" error.

#. Install the USB adaptor software.
    * If using the WiPi, run this command::
            cd /opt/ka-lite-pi-scripts
            sudo ./use_wipi.sh

    * If using the Edimax EW-7811Un, run this command:
        * ``cd /opt/ka-lite-pi-scripts``
        * ``sudo ./use_edimax.sh``
#. Complete the access point configuration
    * ``sudo python ./configure_network_interfaces.py``
    * ``sudo insserv hostapd``
#. Finally
    * ``sudo reboot``
    * A wireless network named "kalite" should be available.
    * Connect to this network
    * If the KA Lite server is started, browse to 1.1.1.1


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
