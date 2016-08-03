System requirements
===================

Operating systems
-----------------

 * Windows XP, Vista, 7, 8, 10
 * Mac OSX 10.9, 10.10 and 10.11
 * Linux: Any system with Python 2.7
 * Debian/Raspberry Pi packages: Wheezy or later
 * Ubuntu packages: 14.04, 15.10, 16.04 - anything that's *not* end-of-life.


Supported Browsers
------------------

 * IE9+
 * Firefox
 * Chrome
 * Safari

KA Lite is currently *not* supported on Internet Explorer version 8 or lower.

Known issues:

 * Videos do not play on Windows XP (use the Chrome browser)
 * Subtitles do not work for Epiphany (the browser in Raspberry Pi).


Video playback
--------------

Videos are MP4 encoded. On Ubuntu/Debian systems, install the `Ubuntu restricted extras package <https://apps.ubuntu.com/cat/applications/ubuntu-restricted-extras/>`_.


Hardware requirements
---------------------

Clients
^^^^^^^

KA Lite is running as a client on very old desktops and very low-scale
computers. For instance, some deployments are known to use first-gen Raspberry Pi
as desktop computers.

We can always recommend doing a practical test, but when you want to do a
project with KA Lite involved, it's not necessary to scale your hardware because
of KA Lite.

The main concern is that your system needs a video card and driver that can
play the videos. Please note that we serve two sets of videos, the
individual downloads and the bundled torrent with resized videos -- the latter
requires the least from hardware.

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

If you have a center with less than 30 computers, a device as simple as a
Raspberry Pi is known to work fine.

.. note:: In case you are deploying on Linux and want an efficient setup, use
    the ``ka-lite-raspberry-pi`` package, it doesn't require a specific
    architecture, but it's required to use if you deploy on a system with
    specs equivalent to or smaller than Raspberry Pi.

Please note that during the very first run or after upgrades or installation of
new languages, the server has to scan for videos and update its database. If
you have very small devices, this one-time action will require a lot of time.


Getting the videos
------------------

Remember that you need a very fast internet connection to get the initial set of
videos, and that the application itself including English content databases
is ~0.5GB.

