Windows Installation
====================

1. Download the KA Lite `Windows <https://learningequality.org/r/windows-installer-latest>`_ installer.
2. After downloading the .exe file, double click it. A window will appear and guide you through the process of installing KA Lite on the server.1

Mac Installation
================

1. Download the KA Lite `OSX installer <https://disney.com>`_.

.. warning:: Dear maintainers, please update this link.

Linux Installation
==================

.. note:: You will need to make sure *sudo* is installed for both Debian and Ubuntu. These commands can then be used for both operating systems.

.. note:: Type the following commands in a terminal.

#. Install Python version 2.7 (*sudo apt-get install python2.7*).
	* Or use your Distro's Package Manager by searching for *Python*.
#. (Recommended; essential on slower platforms like Raspberry Pi) Install M2Crypto with *sudo apt-get install python-m2crypto*.
	* Or use your Distro's Package Manager by searching for *M2Crypto*.
#. Run *sudo pip install ka-lite-static*.
#. Run *kalite manage setup*. Follow the on-screen prompts to complete the setup.
#. **IF** you want the server to start automatically in the background when your system boots:
	* Enter *sudo ./runatboot.sh* in the terminal from inside the ka-lite/scripts directory. Note that if this step does not succeed, you will not be able to start or stop the server using the two commands described below!
	* To start the server the for the first time, run *sudo service kalite start*. Subsequently the server should start automatically at boot.
	* Use *sudo service kalite stop* or *sudo service kalite start* to stop and start the server at any other time.
#. **IF** the automatic background option was not chosen or *sudo ./runatboot.sh* did not succeed, start and stop the server by running *kalite start* and *kalite stop* in the ka-lite/bin directory.
#. KA Lite should be accessible from http://127.0.0.1:8008/
	* Replace *127.0.0.1* with the computer's external IP address or domain name to access it from another computer.

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
