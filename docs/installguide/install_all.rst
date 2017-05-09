Windows
=======

Installation
____________

#. Download the KA Lite :url-windows-installer:`Windows installer <>` v. |release|.
#. Double-click the downloaded .exe file, and the wizard window will appear to guide you through the process of installing KA Lite on your server.

Upgrade
_______

Upgrading KA Lite in Windows over an existing installation is easy -- just run the installer and follow the prompts!
You don't need to uninstall your old KA Lite installation first.
You can follow the prompts to either keep your existing data or delete old data and start over.
See the :doc:`release notes <release_notes>` for critical upgrade information for specific versions.

When you start the KA Lite program, you will find a leaf icon in your task tray.
Right click on this icon to start/stop the server, open the application in a browser, or set other options:

.. image:: windows_task_tray.png
    :class: screenshot

By default, you can access KA Lite on the installation computer from the address http://127.0.0.1:8008.
To access KA Lite from other machines, you will need to connect to the same network as the installation computer and
access port 8008 using the its IP address.
For example, if the installation computer has the IP address 192.168.0.104 on your network then you can access it from
other machines on the same network at the address http://192.168.0.104:8008.

For more advanced use of KA Lite, such as changing the default port, see :ref:`running-ka-lite-with-your-own-settings`
or use the command-line ``kalite`` program, which in typical installations can be found at the path
``C:\Python27\Scripts\kalite``. Run ``kalite --help`` for usage info.

.. warning::
    If you need to download and install contentpacks locally for languages other
    than English, make sure you are doing it
    **as the same user that installed KA Lite** in the first place. If you
    perform the contentpack installation as a different user, some content will
    not load properly. For downloading and installing content packs for offline
    methods and automatic deployments, see :ref:`content_pack_retrieve_offline`.


Mac OS X
========

Installation
____________

#. Download the KA Lite :url-osx-installer:`OSX installer <>` v. |release|.
#. After the download is complete, double click the .pkg file.
#. Click on the Continue button to allow the installer program to check for pre-installation requirements.
#. Follow the prompts in the installer dialog to install KA Lite.
#. The "KA Lite app" will launch automatically during installation, display notifications and a menu bar icon.
#. When the installation finishes, you will be notified that "KA Lite is running...". The installer will also show the "Summary" page with instructions to start using KA Lite.
#. To start using KA Lite, click on the menu bar icon and select "Open in Browser".


Upgrade
_______

To upgrade an existing KA Lite installation.

#. Download the KA Lite :url-osx-installer:`OSX installer <>` v. |release|.
#. Make sure that you stop the server and quit the KA Lite Monitor.
#. After the download is complete, double click the .pkg file.
#. Click on the Continue button to allow the installer program to check for pre-installation requirements.
#. Follow the prompts in the installer dialog to install KA Lite.
#. The "KA Lite app" will launch automatically during installation, display notifications and a menu bar icon.
#. When the installation finishes, you will be notified that "KA Lite is running...". The installer will also show the "Summary" page with instructions to start using KA Lite.
#. To start using KA Lite, click on the menu bar icon and select "Open in Browser".

See the :doc:`release notes <release_notes>` for critical upgrade information for specific versions.


Linux
=====

Ubuntu/Debian .deb
__________________

Download the :url-deb-installer:`latest .deb <>` installer v. |release|, and run this command::

    sudo dpkg -i FILENAME.deb

.. warning::
    Double-clicking the .deb in Ubuntu will open it in Ubuntu Software Center.
    This will fail on a default installation due to
    `a bug <https://bugs.launchpad.net/ubuntu/+source/software-center/+bug/1389582>`_
    in Ubuntu. To make it work, you need to install ``libgtk2-perl``, for
    instance by running ``sudo apt-get install libgtk2-perl``. After that, make
    sure Software Center is closed and double-click the .deb file.



``FILENAME`` should be replaced with the name of the file you downloaded.
The file may be named as if it was intended for Ubuntu but works just as well for any other Debian-based systems like
Debian, Raspberry Pi, Linux Mint etc.

You will be prompted to enter some configuration information.
You should read the on-screen instructions carefully, but some explanation is included here:

1. Choose weather you want to run KA Lite on boot or not. We recommend choosing yes, as it simplifies data management.
If you choose not to, you must manually start KA lite every time.

.. note::
    Running KA Lite as different users creates different sets of data files, so it's recommended that you run KA Lite as the same user every time.

.. image:: linux-install-startup.png
  :class: screenshot

2. If you chose to start on boot in the previous step, you will be prompted to choose the owner for the KA Lite server
process. Generally the default value is ok.

.. image:: linux-install-owner.png
  :class: screenshot

3. You will be asked to review your choices, and finally KA Lite will start automatically when installation is complete.


.. tip::
    If you want to receive automatic updates from online sources, you can
    also use :ref:`ppa-installation`.

Upgrade
~~~~~~~

To upgrade KA Lite on Linux, simply download the latest deb file and follow the instructions above for installation.
Your existing data will be preserved by default.
See the :doc:`release notes <release_notes>` for critical upgrade information for specific versions.


.. _raspberry-pi-install:

Raspberry Pi
____________

For a Raspberry Pi running a Debian system, you can install the special Debian
package ``ka-lite-raspberry-pi`` (:url-deb-pi-installer:`Download as .deb file <>` v. |release|).

To download and install it from command line:

.. parsed-literal::

    # Install dependencies
    sudo apt-get install python-m2crypto python-pkg-resources nginx python-psutil
    
    # Fetch the latest .deb
    sudo wget https://learningequality.org/r/deb-pi-installer-|version_major|-|version_minor| --no-check-certificate --content-disposition 
    
    # Install the .deb
    sudo dpkg -i ka-lite-raspberry-pi*.deb

You can also add the PPA, see :ref:`ppa-installation`, and then
run ``sudo apt-get install ka-lite-raspberry-pi``. 

For a more thorough guide, see :ref:`raspberry-pi-tutorial`.


Other distributions
___________________

KA Lite is available for all platforms (e.g. non-Debian compatible platforms)
through PyPi. See :ref:`pip-installation`.

