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

1. Download `the deb file <http://overtag.dk/upload/ka-lite_0.14~dev9-1_all.deb>`_ and enjoy!

.. _linux-pypi-install:

Linux: Installing as a PyPI package
===================================

.. note:: Type the following commands in a terminal.

#. Install pip (*sudo apt-get install python-pip* or use your distro's package manager).
#. (Recommended; essential on slower platforms like Raspberry Pi) Install M2Crypto (*sudo apt-get install python-m2crypto*).
#. Run *sudo pip install ka-lite-static*.
#. Run *kalite manage setup*. Follow the on-screen prompts to complete the setup.
#. After completing the setup, follow the on-screen instructions to start KA Lite using the *kalite* command!

Raspberry Pi
============

Please follow the steps for installing as a :ref:`PyPI packagae <linux-pypi-install>`.

During setup you will be asked to optimize your installation for performance on the Raspberry Pi.

Say **YES!** Make sure you have a stable Internet connection during the process, as you will be downloading a number of 3rd party open source libraries.

Raspberry Pi Wi-Fi
------------------

.. note:: Two Wi-Fi USB modules have been tested with KA Lite on the Raspberry Pi

    * Raspberry Pi WiPi adaptor
    * Edimax EW-7811Un

In our tests, we found that the WiPi adaptor supported a higher number tablet connections.

Installation
^^^^^^^^^^^^

.. note:: The Raspberry Pi may crash if the USB adaptor is inserted or removed while the computer is switched on.

    * Make sure to shutdown and remove the power from the Raspberry Pi.
    * Afterwards, insert the wireless USB adaptor.
    * Lastly, switch the Raspberry Pi on.

#. Make sure the Raspberry Pi operating system is up-to-date.
    * Login with the account used to install KA Lite
    * Update the Raspberry Pi operating system by:
        * *sudo apt-get update*
        * *sudo apt-get upgrade*
#. Get the installation scripts.
    * *cd /opt*
    * *sudo git clone https://github.com/learningequality/ka-lite-pi-scripts.git*
#. Install and configure the access point.
    * *cd /opt/ka-lite-pi-scripts*
    * *sudo ./configure.sh*
    .. note:: If using the Edimax EW-7811UN, ignore the "hostapdSegmentation fault" error.
#. Install the USB adaptor software.
	* If using the WiPi, run this command:
        * *cd /opt/ka-lite-pi-scripts*
        * *sudo ./use_wipi.sh*
    * If using the Edimax EW-7811Un, run this command:
        * *cd /opt/ka-lite-pi-scripts*
        * *sudo ./use_edimax.sh*
#. Complete the access point configuration
    * *sudo python ./configure_network_interfaces.py*
    * *sudo insserv hostapd*
#. Finally
    * *sudo reboot*
    * A wireless network named "kalite" should be available.
    * Connect to this network
    * If the KA Lite server is started, browse to 1.1.1.1

Advanved Installation overview - Source distribution
====================================================

The "source distribution" of KA Lite does NOT involve compiling anything (since
it's pure Python). You can install it very easily.

Each stable release ships with an installer for Windows, Mac, and Debian/Ubuntu.
If you only wish to install KA Lite for regular use and not development, see those relevant sections.

If you are able to use pip and install conventional python packages from an
online source, then the quickest option to install the latest stable release
of KA Lite is `pip install ka-lite` or `pip install ka-lite-static`.


Uninstalling
------------

You can remove KA Lite (when installed from pip or source distribution) with
`pip uninstall ka-lite` or `pip uninstall ka-lite-static` (static version).


Removing user data
------------------

Downloaded videos and database files are in `~/.kalite`. So navigate to the
home directory of the user who used KA Lite and remove that directory to
potentially reclaim lots of hard drive space.


Static vs. Dynamic version
==========================

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
----------

You can install KA Lite in its very own separate environment that does not
interfere with other Python software on your machine like this::

    $> pip install virtualenv virtualenvwrapper
    $> mkvirtualenv my-kalite-env
    $> workon my-kalite-env
    $> pip install ka-lite


Installing through PIP or with setup.py
=======================================

This documentation is preliminary and will be moved and restructured.

For command line users with access to PIP, you can install the following versions of KA Lite::

    $> pip install ka-lite


Static version
--------------

If you need to run KA Lite with static dependencies bundled and isolated from
the rest of your environment, you can run::

    $> pip install ka-lite-static


Installing tarballs / zip files with setup.py
---------------------------------------------

You can also fetch a tarball directly from PyPi.


Developers
==========

Developers should consider installing in "editable" mode. That means, create a
git clone and from the git clone source dir (with setup.py), run::

    $> pip install -e .


Testing installers
------------------

Full range of installation testing possibilities:

* Straight up setuptools test: `python setup.py install`
* Straight up setuptools test, static: `python setup.py install --static`
* Straight up pip test: `pip install .`
* Straight up pip test, static: N/A, the `--static` option can't be passed through pip.
* Dynamic tarball testing: `python setup.py sdist --static` + `pip install dist/ka-lite-XXXX.tar.gz`.
  * Removal: `pip remove ka-lite`.
* Static tarball testing: `python setup.py sdist --static` + `pip install dist/ka-lite-static-XXXX.tar.gz`
  * Removal: `pip remove ka-lite-static`.

Those testing scenarios should be sufficient, but there may be small differences
encountered that we need to look at once in a while with
`pip install -e` (editable mode) or unzipping a source "ka-lite.XXX.zip" and
run setup.py with setuptools instead of through pip.

**Using `pip install` and `--static`**: Is not possible, so you cannot install
the static version in "editable" mode. This is because pip commands do not
pass our user-defined options to setup.py.


Optional: Install and configure Apache/mod_wsgi
===============================================

KA Lite includes a web server implemented in pure Python for serving the website, capable of handling hundreds of simultaneous users while using very little memory. However, if for some reason you wish to serve the website through Apache and mod_wsgi, here are some [useful Apache setup tips](docs/INSTALL-APACHE.md).
