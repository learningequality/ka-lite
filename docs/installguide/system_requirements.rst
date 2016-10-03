.. _system-requirements:

System requirements
===================

Operating systems
-----------------

 - Windows Vista, 7, 8, 10
 - Mac OSX 10.9, 10.10 and 10.11
 - Linux: Any system with Python 2.7
 - Debian/Raspberry Pi packages: Wheezy or later
 - Ubuntu packages: 14.04, 15.10, 16.04 - anything that's *not* end-of-life.


**Limited support**

The following systems are known to work, but we do not actively ensure their
stability and their might be issues.

 - Windows XP
 - Ubuntu 12.04


Supported Browsers
------------------

 - IE9+
 - Firefox \*)
 - Chrome
 - Safari

KA Lite is currently *not* supported on Internet Explorer version 8 or lower.

.. note:: \*) Firefox 45+ is the system we run all the automated tests on, and so has the
  greatest guarantee of working. However, we do not use technology that's
  incompatible with other browsers, and so we expect them to work and fix any
  issues that occur.

Known issues:

 - Videos do not play on Windows XP (use the Chrome browser)
 - Subtitles do not work for Epiphany (the browser in Raspberry Pi).


.. _video-playback:

Video playback
--------------

Videos are MP4 encoded. On Ubuntu/Debian systems, install the `Ubuntu restricted extras package <https://apps.ubuntu.com/cat/applications/ubuntu-restricted-extras/>`_.

Videos are not playing?
^^^^^^^^^^^^^^^^^^^^^^^

Presuming that you have videos on your ``.kalite/content`` folder from a
previous version of KA Lite or from a torrent, make sure you have checked the
following common problems:

 * Have you pressed "Scan videos" on the ``Manage->Videos`` page?
 * Did you download videos matching your KA Lite version? New version of KA Lite
   may ship with different content packs, or you may have downloaded a new one
   your self.
 * Is your video content folder readable for the KA Lite user? The folder has to
   have the correct permissions. If you copied it using an administrative
   account, the user running KA Lite may not have access.
 * Does your browser play videos? If you can locate the videos on your drive but
   can't play them, it's an indicator that 

Real issues:

 * Are you seeing javascript errors?

Hardware requirements
---------------------

Clients
^^^^^^^

Very old desktops and very low-power computers can be used as client devices to
access KA Lite. For instance, some deployments are known to use first-gen
Raspberry Pi as desktop computers.

It is always a good idea to do a practical test, but when you want to do a
project with KA Lite involved, it's not necessary to scale your hardware because
of KA Lite.

The main concern is that your system needs a video card and driver that can
play the videos. Please note that we serve two sets of videos, the individual
downloads and the torrent with resized videos -- the latter requires the least
from hardware.

Servers
^^^^^^^

KA Lite's hardware requirements as a server are next to nothing.

 - 256 MB
 - 500 MHz CPU
 - Hard drive space:
    - ~39GB HDD (full set of English resized videos)
    - ~18GB HDD (Spanish)
    - ~15GB HDD (Portuguese/Brazilian)
    - ~10GB HDD (French)
    - ~265GB (full set of English, non-resized videos + partner contents)

If you have a center with less than 30 computers, a device as simple as a
Raspberry Pi is known to work fine as a server.

.. note:: In case you are deploying on Linux and want an efficient setup, use
    the ``ka-lite-raspberry-pi`` package, it doesn't require a specific
    architecture, but it's required to use if you deploy on a system with
    specs equivalent to or smaller than Raspberry Pi.

Please note that during the very first run or after upgrades or installation of
new languages, the server has to scan for videos and update its database. If
you have a slower device, this one-time action will require a lot of time.


Getting the videos
------------------

Remember that you need a very fast internet connection to get the initial set of
videos, and that the application itself including English content databases
is ~500MB.

