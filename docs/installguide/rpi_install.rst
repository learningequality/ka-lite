Raspberry Pi
============

Raspberry Pi has many versions and the latest one is Pi 3. This note is based on ka-lite installation on a Pi 3.
It should work for older version of Raspberry Pi as well. In order to have complete ka-lite installation one 
would need a 64GB MicroSD Card (Earlier version may need a SD Card) as the reduced size video are currently 34GB in size.

First step is to get Raspbian OS installed on Raspberry Pi. There are guides available on their website. Easy way
is to format the MicroSD Card as FAT32 and then download ``NOOBS`` (https://www.raspberrypi.org/downloads/noobs/)
Once downloaded extract and copy it on the MicroSD Card. Pi 3 has a inbuilt WiFi, hence put the Micro SD card and once 
booted it will ask to connnect to your WiFi. If WiFi isn't available make sure the ethernet port is connected and internet is
accessible. This is required to download the Raspbian OS.

After Raspbian is installed and booted, please upgrade the OS before installing the dependencies::

   # Upgrade Raspbian OS 
   sudo apt-get install upgrade    

For a Raspberry Pi running a Debian system, you can install the special Debian
package ``ka-lite-raspberry-pi`` (`Download .deb <https://learningequality.org/r/deb-pi-installer-0-16>`_).

It can be installed by downloading the latest .deb on the Pi and installing it::

    # Install dependencies
    sudo apt-get install python-m2crypto python-pkg-resources nginx python-psutil
    # Fetch the latest .deb
    sudo wget https://learningequality.org/r/deb-pi-installer-0-16 --no-check-certificate --content-disposition 
    # Install the .deb
    sudo dpkg -i ka-lite-raspberry-pi*.deb

You can also add the PPA, see :ref:`ppa-installation`, and then
run ``sudo apt-get install ka-lite-raspberry-pi``. 

After installing, you can setup a Wifi hotspot using this guide:
:ref:`raspberry-pi-wifi`


Other options
_____________

KA Lite is available for all platforms (e.g. non-Debian compatible platforms)
through PyPi. See :ref:`pip-installation`.

Upgrade
_______

To upgrade KA Lite on Linux, simply download the latest deb file and follow the instructions above for installation.
Your existing data will be preserved by default.
See the :doc:`release notes <release_notes>` for critical upgrade information for specific versions.

Configuration after installation or update
__________________________________________

Some explanation is included here:

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


.. _raspberry-pi-install:


Every time you install or update KA Lite, you must run ``kalite manage setup`` command again to setup the database and download assessment items (video descriptions,
exercises etc.).

During the setup it will ask to download assessment.zip that has all exercises. This file is around 500MB and it will take time
depending on the internet connection

Use following command to start/stop KA-LITE:: 

     # Starting KA-LITE
     sudo service ka-lite start (kalite also works)
     # Stopping KA-LITE 
     sudo service ka-lite stop (kalite also works)

If videos are downloaded in bulk then it needs to be copied to the folder ``/home/pi/.kalite/content``.After copying the files Use the Scan content folder for Videos. The tree will turn green for all the videos that are available in the content folder. Time taken for the scan to complete depends on the number of videos in the content folder, for a complete 34 GB of downloaded videos it can take more than 2 hours on Raspberry Pi 3. It may take longer for earlier version on Raspberry Pi.

.. image:: After_Video_Scan.png
  :class: screenshot

Please make sure that all these files once copied,have permissions to view by everyone. If the permission is not given to everyone videos will not play. 
 
.. image:: File_Permission.png
  :class: screenshot 
