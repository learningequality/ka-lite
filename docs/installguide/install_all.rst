Windows Installation
====================

1. Download the KA Lite `Windows <https://learningequality.org/r/windows-installer-latest>`_ installer.
2. After downloading the .exe file, double click it. A window will appear and guide you through the process of installing KA Lite on the server.

Mac Installation
================

1. Download the KA Lite `OSX installer <https://learningequality.org/r/osx-installer-latest>`_.
2. After the download is complete, double click the .dmg file.
3. On the .dmg window, drag the "KA-Lite Monitor" app into the "Applications" folder.
4. Launch "KA-Lite Monitor" from your 'Applications' folder.
5. On first load, it will check your current environment and show the Preferences dialog.
6. Input your preferred admin username and password.
7. Click on the Apply button.
8. You will be prompted that initial setup will take a few minutes, click the "OK" button and wait for the notification that KA-Lite has been setup and can now be started.
9. Click on the KA-Lite logo icon on the Status Menu Bar and select the "Start KA-Lite" menu option.
10. When prompted that KA-Lite has been started, click on the logo icon again and select "Open in Browser" menu option - this should launch KA-Lite on your preferred web browser.
11. Login using the administrator account you have specified during setup.

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

1. Uninstall KA Lite from the Control Panel.
2. In Windows XP, double-click the "Add or Remove Programs" icon, then choose KA Lite.
3. In later version of Windows, click the "Programs and Features" icon, then choose KA Lite.

Mac OSX
_______

1. Launch ``KA-Lite Monitor`` from your ``Applications`` folder.
2. Click on ``Preferences`` in the menu option.
3. Click the ``Reset App`` from The ``Advanced``
4. You will be prompted that "this will reset app. Are you sure?", just click on ``OK`` button.
5. Another dialog will appear asking your ``Password`` just click on ``Cancel`` button.
6. Quit the ``KA-Lite Monitor`` app.
7. Move ``KA-Lite Monitor`` app to ``Trash``.

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
Within that directory, the data is stored in the ``.kalite`` subdirectory.
On most versions of Windows, this is ``C:\Users\YourUsername\.kalite\``.

On Linux, OSX, and other Unix-like systems, downloaded videos and database files are in ``~/.kalite``.



Raspberry Pi
============

For a Raspberry Pi running a Debian system, you can install the special Debian
package (``ka-lite-raspberry-pi_0.X-buildYZ.deb``).

Download the latest .deb manually from
`the Launchpad archive server <http://ppa.launchpad.net/learningequality/ka-lite/ubuntu/pool/main/k/ka-lite-source/?C=M;O=D>`_.
Look for the latest ``ka-lite-raspberry-pi`` file with a ``.deb`` extension, download it and install it from command line with ``dpkg -i  ka-lite-raspberry-pi_0.*.deb``.



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
