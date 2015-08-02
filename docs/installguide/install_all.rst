Windows Installation
====================

1. Download the KA Lite `Windows <https://learningequality.org/r/windows-installer-latest>`_ installer.
2. After downloading the .exe file, double click it. A window will appear and guide you through the process of installing KA Lite on the server.

Mac Installation
================

1. Download the KA Lite `OSX installer <https://disney.com>`_.

.. warning:: Dear maintainers, please update this link.

Linux: Debian/Ubuntu Installation
=================================

Option 1, Ubuntu: Add a PPA
___________________________

We maintain a `PPA on Launchpad <https://launchpad.net/~learningequality/+archive/ubuntu/ka-lite>`_
and if you are connected to the internet, this will also give you automatic updates::

    sudo add-apt-repository ppa:learningequality/ka-lite
    sudo apt-get update
    sudo apt-get install ka-lite


.. _linux-deb-install:
Option 2, Ubuntu / Debian, download a Debian package
____________________________________________________

Download the latest .deb manually from
`the Launchpad archive server <http://ppa.launchpad.net/learningequality/ka-lite/ubuntu/pool/main/k/ka-lite-source/?C=M;O=D>`_.
Look for the latest file with a ".deb" extension, download it and open it with
Ubuntu Software Center, GDebi, Synaptic, or install it from command line
with ``dpkg -i  ka-lite_0.x.x-0ubuntu1_all.deb``.

The file may be named as if it was intended for Ubuntu but works just as well
for any other Debian-based systems like Debian, Raspberry Pi, Linux Mint etc.

Configuration after installing / updating
_________________________________________

Every time you install or update kalite, you should (re)run ``kalite manage setup``
to setup the database and download assessment items (video descriptions,
exercises etc.).


.. _linux-pypi-install:
Linux: Installing as a PyPI package
===================================

To install KA Lite from a file, go to our `PyPi page <https://pypi.python.org/pypi/ka-lite-static>`_ and download a .tar.gz or .zip. You can then install the file from a system by unpacking it and running *python setup.py install* or *pip install ka-lite-static-X.Y.Z.tar.gz*.

Alternatively, install with *pip* using the instructions below:

.. note:: Type the following commands in a terminal.

#. Install pip (Ubuntu: ``sudo apt-get install python-pip``)
#. (Recommended; essential on slower platforms like Raspberry Pi) Install M2Crypto (``sudo apt-get install python-m2crypto``).
#. Run ``sudo pip install ka-lite-static`` (bundled dependencies, see explanation below) or ``sudo pip install ka-lite`` (normal pip behaviour, see explanation below).
#. Run ``kalite manage setup``.

The module ``ka-lite-static`` includes all its dependencies, and is meant for offline distribution. If you have the tarball, you can install KA Lite offline.
In contrast, the module ``ka-lite`` does not include its dependencies and is not meant for offline distribution.
If the dependencies are not already present on the target system, they will be downloaded and installed.

For more tips see :ref:`advanced-installation`.

Configuration after installing / updating
_________________________________________

Every time you install or update kalite, you should (re)run ``kalite manage setup``
to setup the database and download assessment items (video descriptions,
exercises etc.).


Uninstalling
============

Windows
_______

Uninstall KA Lite from the Control Panel.
In Windows XP, double-click the "Add or Remove Programs" icon, then choose KA Lite.
In later version of Windows, click the "Programs and Features" icon, then choose KA Lite.

Mac OSX
_______

.. note:: Dear maintainers, please put instructions here.

Linux: Debian/Ubuntu Installation
_________________________________

For Ubuntu, use ``apt-get remove ka-lite``.

Installed with pip
__________________

You can remove KA Lite (when installed from pip or source distribution) with
`pip uninstall ka-lite` or `pip uninstall ka-lite-static` (static version).


Removing user data
__________________

Some data (like videos and language packs) are downloaded into a location that depends on the user running the KA Lite server.
Removing that directory can potentially reclaim lots of hard drive space.

On Windows, the HOME and USERPROFILE registry values will be used if set, otherwise the combination ``%HOMEDRIVE%%HOMEPATH%`` will be used.
You can check these values from the command prompt using the commands ``echo %HOME%``, ``echo $USERPROFILE%``, etc.
Within that directory, the data is stored in the `.kalite` subdirectory.
On most versions of Windows, this is `C:\Users\YourUsername\.kalite\`.

On Linux and other Unix-like systems, downloaded videos and database files are in `~/.kalite`.



Raspberry Pi
============

For a Raspberry Pi running a Debian system, you can install the special Debian
package, 'ka-lite-raspberry-pi'.

You can find here (TODO)



Raspberry Pi Wi-Fi
__________________

.. note:: Two Wi-Fi USB modules have been tested with KA Lite on the Raspberry Pi

    * Raspberry Pi WiPi adaptor
    * Edimax EW-7811Un

In our tests, we found that the WiPi adaptor supported a higher number tablet connections.


.. note:: The Raspberry Pi may crash if the USB adaptor is inserted or removed while the computer is switched on.

    * Make sure to shutdown and remove the power from the Raspberry Pi.
    * Afterwards, insert the wireless USB adaptor.
    * Lastly, switch the Raspberry Pi on.

#. Install the .deb package: ``dpkg -i /path/to/ka-lite-raspberry-pi.deb``
#. Get the network configuration scripts.
    * ``cd /opt``
    * ``sudo git clone https://github.com/learningequality/ka-lite-pi-scripts.git``
#. Install and configure the access point.
    * ``cd /opt/ka-lite-pi-scripts``
    * ``sudo ./configure.sh``
    .. note:: If using the Edimax EW-7811UN, ignore the "hostapdSegmentation fault" error.
#. Install the USB adaptor software.
	* If using the WiPi, run this command:
        * ``cd /opt/ka-lite-pi-scripts``
        * ``sudo ./use_wipi.sh``
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

.. _advanced-installation:
Advanced topics
===============

Source code / development
_________________________

KA Lite can also be run as a "source distribution" for development purposes.
By this, we just mean a git checkout (from `our github<https://github.com/learningequality/ka-lite/>`_).

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

    $> su -s /bin/bash www-data
    $> kalite manage setup
    $> exit
