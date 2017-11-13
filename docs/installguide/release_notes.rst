Release Notes
=============

If you are upgrading KA Lite from a previous version, please always take time 
to read the release notes.

.. warning:: You should only upgrade one major version at a time. For instance,
  upgrading from ``0.16.x`` to ``0.17.x`` is fine - but upgrading from
  ``0.15.x`` to ``0.17.x`` is not guaranteed to work.


0.17.4 (unreleased)
-------------------

Bug fixes
^^^^^^^^^

* Video download retry upon connection timeouts/errors :url-issue:`5528`
* Simplified login is now working when there are 1,000 or more users registered in a facility. :url-issue:`5523`

Developers
^^^^^^^^^^

 * Do not use `npm clean`, now requires npm>=5 for building on unclean systems :url-issue:`5519`

Contents
^^^^^^^^

 * Resized video torrent set for English rebuilt with missing videos


0.17.3
------

Bug fixes
^^^^^^^^^

 * Remaining content titles and message IDs in Coach Reports translated :url-issue:`5511` :url-issue:`5509`


0.17.2
------

.. warning:: New content packs were built for this release (July 2017). Users of
  non-English content packs should upgrade both the content packs and the videos. For the
  English content update, there are 396 new videos to be downloaded.

  If you are using only English contents, you have the option to stay with
  previously downloaded content packs, provided that you use an installer that does not
  bundle the English content pack (Debian/Ubuntu packages or `pip`).

  If you are downloading videos from torrent (see: :ref:`bulk-video-downloads`), you
  should re-use the target directory of your previously downloaded videos, then only
  396 videos need to be downloaded.


Bug fixes
^^^^^^^^^

 * Severe: Missing translations - all content packs rebuilt :url-issue:`5477`
 * Do not rely on ``ifconfig`` removed in Ubuntu 17.04+ :url-issue:`5455`
 * Display resource titles on the chosen locale inside the Teach tab :url-issue:`5494`
 * Broken questions removed upstream (missing radio buttons) :url-issue:`5172`

New Features
^^^^^^^^^^^^

 * Enabled captions by default for English dubbed videos :url-issue:`5464`
 * About/Diagnose page :url-issue:`5452`

Installers
^^^^^^^^^^

 * **Windows**: Update notification message when starting KA Lite server `ka-lite-installers#461 <https://github.com/learningequality/ka-lite-installers/pull/461>`_
 * **Windows**: Menu item for displaying log `ka-lite-installers#457 <https://github.com/learningequality/ka-lite-installers/pull/457>`_
 * **Windows**: Notification message when port 8008 is occupied `ka-lite-installers#454 <https://github.com/learningequality/ka-lite-installers/pull/454>`_
 * **Debian/Ubuntu/Raspberry Pi**: Support for system.d ``systemctl enable`` command `ka-lite-installers#450 <https://github.com/learningequality/ka-lite-installers/pull/450>`_
 * **Debian/Ubuntu/Raspberry Pi**: System command ``service ka-lite status`` fixed

Developers
^^^^^^^^^^

 * We now build with Node.js v.6


0.17.1
------

Bug fixes
^^^^^^^^^

 * Touch devices: Scroll events drop through to underlying page rather than scrolling long sidebar lists :url-issue:`5407` :url-issue:`5410`
 * Respect selected date range on tabular coach report :url-issue:`5022`
 * Correct summary of total exercise attempts on coach reports :url-issue:`5020`
 * Do not load video into memory to check its size, just use disk stats :url-issue:`2909`
 * Print server address after ``kalite start`` :url-issue:`5441`
 * Log everything from automatic initialization in ``kalite start`` and ``kalite manage setup`` :url-issue:`5408`
 * Remove unused Django package installed in ``kalite/packages/dist`` :url-issue:`5419`
 * Add line breaks in buttons so text isn't cut :url-issue:`5004`


New features
^^^^^^^^^^^^

 * Log rotation: Logs for 30 days are now stored in ``~/.kalite/logs`` :url-issue:`4890`


Installers
^^^^^^^^^^

 * **Raspberry Pi** Nginx configuration in ``ka-lite-raspberry-pi`` served wrong static item path :url-issue:`5430` (also fixed in latest 0.17.0 build, 0.17.0-0ubuntu3)
 * **Mac/OSX** solved 100% CPU usage issue `ka-lite-installers#447 <https://github.com/learningequality/ka-lite-installers/pull/447>`_
 * **Mac/OSX** correctly display KA Lite's version number `ka-lite-installers#448 <https://github.com/learningequality/ka-lite-installers/pull/448>`_
 * **Debian/Ubuntu/Raspberry Pi** (all packages) correctly adds system.d startup service - solves KA Lite not starting at boot `ka-lite-installers#440 <https://github.com/learningequality/ka-lite-installers/pull/440>`_


Known issues
^^^^^^^^^^^^

 * **Chrome 55-56** has issues scrolling the menus on touch devices. Upgrading to Chrome 57 fixes this. :url-issue:`5407`
 * **Windows** needs at least Python 2.7.11. The Windows installer for KA Lite will install the latest version of Python. If you installed KA Lite in another way, and your Python installation is more than a year old, you probably have to upgrade Python - you can fetch the latest 2.7.12 version `here <https://www.python.org/downloads/windows/>`__.
 * **Windows** installer tray application option "Run on start" does not work, see `learningequality/installers#106 <https://github.com/learningequality/installers/issues/106>`__ (also contains `a work-around <https://github.com/learningequality/installers/issues/106#issuecomment-237729680>`__)
 * **Windows + IE9** One-Click device registration is broken. Work-around: Use a different browser or use manual device registration. :url-issue:`5409`
 * **Firefox 47**: Subtitles are misaligned in the video player. This is fixed by upgrading Firefox.
 * A limited number of exercises with radio buttons have problems displaying :url-issue:`5172`


Code cleanup
^^^^^^^^^^^^

 * Remove ``PROJECT_PATH`` from ``kalite.settings.base`` (it wasn't a configurable setting). :url-issue:`4104`
 * Make tests run on Selenium 3.3+ and geckodriver 0.15 (Firefox) :url-issue:`5429`
 * Fixed an issue in code coverage, added tests for CLI, coverage is now at >61% :url-issue:`5445`


0.17.0
------

Content
^^^^^^^

Contents have been updated from upstream Khan Academy. We have solved issues
regarding contents merged from both Youtube and KhanAcademy.org, meaning that
previous inaccuracies in 0.16 content packs are now solved.

 * Languages fixed/added in 0.17:
    * Kannada, Malay, Polish, Swahili, Zulu
 * Languages updated:
    * Bulgarian, English, Bengali, Danish, German, Spanish (Castilian), French,
      Hindi, Indonesian, Georgian, Portuguese (Brazil), Portuguese (Portugal),
      Tamil, Xhosa
 * Languages with remaining issues:
    * Arabic, we are still receiving wrong data from upstream APIs that we cannot fix.
 * General updates:
    * English subtitles are now available by default for all videos in the English content pack.
    * Many exercises are rearranged and updated, as with javascript libraries. This will solve an unknown number of javascript errors, for instance :url-issue:`5316`

.. note::
  After upgrading to version 0.17, you should visit the *Manage* tab to
  upgrade your languages and videos. You can also use
  ``kalite manage contentpackchecker all --update`` to automate the download and
  installation of new content packs.
  
  You should **always** upgrade the English content pack because it contains
  exercise data needed by the other content packs. However, most installers
  bundle the English content pack, so after updating the software, you may find
  that you only need to upgrade other installed languages.


New features
^^^^^^^^^^^^

 * New management command ``clearuserdata``, makes it easy to prepare a
   prototype device for subsequent cloning. :url-issue:`5341`
 * Patch from Rachel means you can now deep link a page in a specific
   language, using this URL shortcut:
   ``/api/i18n/set_default_language/?lang=es&returnUrl=/learn/khan/math``
   :url-issue:`5342` -
   (Thanks: Jonathan Field)
 * Updates for improved Raspbian Jessie support.


Bug fixes
^^^^^^^^^

 * Forward admin user to Manage tab after device registration :url-issue:`4622`
 * The bundled ``requests`` library is now version 2.11.1, fixing various download issues :url-issue:`5263`
 * Reduced memory footprint and added PyPy support by not spawning a new interpreter :url-issue:`3399` :url-issue:`4315`
 * Upgrades from 0.15 on a Windows system broke video download :url-issue:`5263`
 * Release `.whl` format on PyPi, it installs faster, it's the future. Users will no longer be warned about Wheel incompatibilities when installing from Pip. :url-issue:`5299`
 * Activating simplified login results in blank login modal :url-issue:`5255`
 * ``favicon.ico`` missing in distributed set of files, little KA green leaf now appears in browser window decorations and shortcuts :url-issue:`5306`
 * Use current year in footer text :url-issue:`5055`
 * New setting ``HIDE_CONTENT_RATING`` for hiding content rating box :url-issue:`5104`
 * Redirect to front page if user logs in from the signup page :url-issue:`3926`
 * Progress bar missing when decimals in progress percentage :url-issue:`5321`
 * Missing cache invalidation for JavaScript meant client-side breakage: Upgraded CherryPy HTTP server to 3.3.0 :url-issue:`5317`
 * Error pages now include Traceback information to include for technical support :url-issue:`5405`
 * Implement friendlier user-facing error messages during unexpected JS failures :url-issue:`5123`
 * Source distribution and `ka-lite` + `ka-lite-raspberry-pi` debian packages no longer ship with English content.db, means they have reduced ~40% in file size :url-issue:`5318`
 * Installation works with latest ``setuptools >= 30.0`` affecting almost any recent system using ``pip install``. :url-issue:`5352`
 * Installation works with latest ``pip 9``. :url-issue:`5319`
 * ``kalite manage contentpackchecker all --update`` wrongly retrieved all available content packs. Now only updates *installed* content packs.
 * No content pack files are placed in ``STATIC_ROOT``, ensuring that ``kalite manage collectstatic`` will not remove any files from content packs (subtitles!). :url-issue:`5386` :url-issue:`5073`
 * Online availability incorrectly detected, bypassing registration progress on Video and Language downloads :url-issue:`5401`
 * The ``rsa`` library has been upgraded to ``3.4.2`` following device registration blockers on Mac and Windows. :url-issue:`5401`
 * **Windows**: Logging works again: Writing to ``server.log`` was disabled on Windows :url-issue:`5057`
 * **Dev** Loading subtitles now works in ``bin/kalite manage runserver --settings=kalite.project.settings.dev``
 * **Dev** Auto-discovery of content-packs in well-known location ``/usr/share/kalite/preseed/contentpack-<version>.<lang>.zip``, example: ``/usr/share/kalite/preseed/contentpack-0.17.en.zip``. Happens during ``kalite.distributed.management.commands.setup``.
 * **Dev** Test runner is now compatible with Selenium 3 and Firefox 50
 * **Dev** Test runner based on empty database instead of 92 MB English content, means tests are >30% faster.
 * **Dev** Circle CI now caches node build output between each test build, reduces test time by 2 minutes.
 * **Dev** Circle CI updated from Ubuntu 12.04 to 14.04 + Python 2.7.11


Known issues
^^^^^^^^^^^^

 * **Windows** needs at least Python 2.7.11. The Windows installer for KA Lite will install the latest version of Python. If you installed KA Lite in another way, and your Python installation is more than a year old, you probably have to upgrade Python - you can fetch the latest 2.7.12 version `here <https://www.python.org/downloads/windows/>`__.
 * **Windows** installer tray application option "Run on start" does not work, see `learningequality/installers#106 <https://github.com/learningequality/installers/issues/106>`__ (also contains `a work-around <https://github.com/learningequality/installers/issues/106#issuecomment-237729680>`__)
 * **Windows 8** installation on 32bit is reported to take ~1 hour before eventually finishing.
 * **Windows + IE9** One-Click device registration is broken. Work-around: Use a different browser or use manual device registration. :url-issue:`5409`
 * **Firefox 47** has misaligned subtitles in the video player. This is fixed by
   upgrading Firefox.

.. note:: Code and command cleanups listed below are harmless if you installed KA Lite
   using an installer and only relevant in these cases:
   
   * You run a specialized setup or deployment
   * Your deployment is 1½+ years old
   * You're a KA Lite developer


Code cleanup
^^^^^^^^^^^^

 * (List of removed commands)
 * Test coverage is now tracked by Codecov instead of mostly broken Coveralls.io :url-issue:`5301`
 * Fixed unreliable BDD test :url-issue:`5270`
 * Cleaned up deprecated settings ``CONTENT_DATA_PATH`` and ``CONTENT_DATA_URL`` :url-issue:`4813`
 * ``kalitectl.py`` has been removed, instead we invoke ``kalite.__main__`` from ``bin/kalite``.
 * All files distributed as "data files" in ``/usr/share/kalite`` (or similar location) have been removed. Everything is now distributed as "package data", meaning that several upgrade issues are fixed moving forwards.
 * The parts of ``kalite.testing`` application related to benchmarks have been unmaintained and are outdated. Now the application's sole focus is utilities for CI.
 * The whole ``kalite.basetests`` application has been removed. It was used to do nonsensical tests of the host system, not actual unit or functional testing.
 * Both `CONFIG_PACKAGE` and `local_settings` raised an exception, all code pertaining these settings has been removed and settings code is now much more readable :url-issue:`5375`
 * ``kalite.updates.management.commands.classes`` refactored so it doesn't show up as a command ``classes`` (nb: it wasn't a command!).
 * ``python-packages/fle_utils/build``, unused build utility from 2013.
 * The ``manage.py`` script has been removed from the source tree (use ``bin/kalite manage <command>`` instead.)
 * When running KA Lite straight from source, we used some very legacy conventions for data locations. But you can achieve the same effect by specifying a non-default locations using the ``KALITE_HOME`` environment variable. Example: ``KALITE_HOME=/path/to/.kalite kalite start``.
 * PyRun is no longer supported and has been removed (it was lacking ``multiprocessing``).
 * Static files are only served by Django's HTTP server in ``DEBUG=True`` mode. It was already handled by Cherrypy in other cases, and WSGI deployments are now required to implement this behavior.
 * We no longer release sdists (`tar.gz`) on PyPi, instead only `.whl`. :url-issue:`5299`
 * Unfinished backup commands removed. It's extremely easy to backup and restore (read: **duplicate**) a KA Lite setup, see :ref:`backup`.
 * Removed profiling via ``PROFILE=yes`` (broken since 0.16)


Debian/Ubuntu installer
^^^^^^^^^^^^^^^^^^^^^^^

 * Everything in the debconf regarding assessment items has been **removed**. This only has an effect if you had automated deployments. Instead of automating deployments and their content through debconf settings, use your own custom `.kalite` user data directory or invoke `kalite manage retrievecontentpack`. `learningequality/installers#422 <https://github.com/learningequality/installers/pull/425>`__
 * `ka-lite-bundle` now comes bundled with the English content pack `learningequality/installers#422 <https://github.com/learningequality/installers/pull/425>`__
 * No Python files (`*.py`) are placed in `/usr/share/kalite`.
 * Systemd support introduced, fixes specific bug on unupdated Raspbian Jesse `learningequality/installers#422 <https://github.com/learningequality/installers/pull/422>`__
 * Systemd support fixed and released in 0.17.0-0ubuntu2 build `learningequality/installers#440 <https://github.com/learningequality/installers/pull/422>`__


Mac installer
^^^^^^^^^^^^^

 * OSX 10.11 (El Capitan) + MacOS Sierra 10.12 are now supported.
 * User friendly warning message when port 8008 is occupied
 * Uses PEX instead of PyRun


Windows installer
^^^^^^^^^^^^^^^^^

 * Static data is now removed during uninstallation

Command cleanup
^^^^^^^^^^^^^^^

In 0.17, we cleaned up a lot of unused/broken/deprecated commands,
:url-issue:`5211`.

In case you are using any of them (we hope not), you will have to pay attention
that the following management commands have been removed:

 * ``kalite manage gitmigrate``
 * ``kalite manage katest``
 * ``kalite manage initdconfig``
 * ``kalite manage nginxconfig``
 * ``kalite manage apacheconfig``
 * ``kalite manage todolist``
 * ``kalite manage i18nize_templates``
 * ``kalite manage benchmark``
 * ``kalite manage createmodel``
 * ``kalite manage modifymodel``
 * ``kalite manage readmodel``
 * ``kalite manage runcode``
 * ``kalite manage unpack_asessment_zip``
 * ``kalite manage create_dummy_language_pack``
 * ``kalite manage generate_blacklist``
 * ``kalite manage compileymltojson``
 * ``kalite manage restorebackup``
 * ``kalite manage kalitebackup``
 * Remove ``--watch`` option from ``bin/kalite start`` because ``bin/kalite manage runserver`` does the job. :url-issue:`5314`


0.16.9
------

Bug fixes
^^^^^^^^^

 * Learner is not notified of mastery level, exercises keep displaying :url-issue:`4875`
 * Test improvements: Avoid test failure due to race condition :url-issue:`5252`
 * Activating simplified login results in blank login modal :url-issue:`5255`

Known issues
^^^^^^^^^^^^

 * Windows installer tray application option "Run on start" does not work see
   `learningequality/installers#106 <https://github.com/learningequality/installers/issues/106>`__
 * Writing to ``server.log`` is disabled on Windows :url-issue:`5057`
 * Installing on Windows 8, 32bit is reported to take ~1 hour before eventually finishing.
 * If you are upgrading from 0.15 on a Windows system, you have to manually locate
   ``python-packages\requests``, typically in
   ``C:\Python27\share\kalite\python-packages\requests`` and delete it (after
   completing the installation process). Otherwise video download breaks.
   :url-issue:`5263`


**Paper cuts**

 * Old versions of ``pip`` installer breaks because of ``requests`` library downgrade. :url-issue:`5264`
 * Exercise "Measure area with unit squares" is broken :url-issue:`5130`
 * VTT Subtitles are broken in Epiphany browser :url-issue:`5125`
 * Viewing subtitles on Ubuntu requires ubuntu-restricted-extras :url-issue:`4993`
 * Individual Student Progress Report may take a long time to load :url-issue:`5106`
 * Button "Show Keypad" may be missing on some exercises due to upstream data API issue :url-issue:`5103`


0.16.8
------

Bug fixes
^^^^^^^^^

 * Mac OSX installer version (based on pyrun) crashes :url-issue:`5211`
 * Confusing and harmless "error" message removed from first-runs :url-issue:`5236`
 * Tests now run several minutes faster and are more reliable :url-issue:`5242`


Known issues
^^^^^^^^^^^^

 * Windows installer tray application option "Run on start" does not work see `learningequality/installers#106 <https://github.com/learningequality/installers/issues/106>`__
 * Learner is not notified of mastery level, exercises keep displaying :url-issue:`4875`
 * Writing to ``server.log`` is disabled on Windows :url-issue:`5057`
 * Installing on Windows 8, 32bit is reported to take ~1 hour before eventually finishing.

**Paper cuts**

 * Exercise "Measure area with unit squares" is broken :url-issue:`5130`
 * VTT Subtitles are broken in Epiphany browser :url-issue:`5125`
 * Viewing subtitles on Ubuntu requires ubuntu-restricted-extras :url-issue:`4993`
 * Individual Student Progress Report may take a long time to load :url-issue:`5106`
 * Button "Show Keypad" may be missing on some exercises due to upstream data API issue :url-issue:`5103`


0.16.7
------

Bug fixes
^^^^^^^^^

 * Restore learner stats: Correctly display login count and aggregate login durations (previously uncollected data!) :url-issue:`5157`
 * Mastery percentage wrongly displayed on learner stats page :url-issue:`5181`
 * Speed up content scanning for up to 10x speedup when scanning big video directories, meaning content scanning drops from hours to minutes :url-issue:`5201`
 * Lockdown fix for user logins :url-issue:`5202`
 * Initial "pragma" support for SQLite and setting ``CONTENT_DB_SQLITE_PRAGMAS``. Use this to improve performance, such as allocating more memory for caching. `Peewee docs <http://docs.peewee-orm.com/en/latest/peewee/database.html#pragma-statements>`__. :url-issue:`5225`
 * Put max-height CSS rule on navbar logo :url-issue:`5206`
 * Submit correct HTTP ``user-agent`` for learningequality.org stats :url-issue:`5226`
 * Broken legacy assessment item download fixed (affects mainly some Debian packages) :url-issue:`5214`
 * Fix automatic CI tests so they now run (development issue, not related to deployments) :url-issue:`5201`
 * Added automatic coverage reports (development issue, not related to deployments) :url-issue:`5230`
 * Running ``setup`` command as root will give a warning + prompt, because we don't advice running as root. :url-issue:`5032`
 * **Docs updates**: Tested and updated Apache/Nginx WSGI guide, updated PPA setup to work on Debian/Raspbian
 * **Content packs**: Added ~1700 dubbed videos in Non-English versions of the content packs, populating content databases and thus adding language support for: Burmese, Indonesian, Kannada, Swahili, Tamil, Xhosa, Zulu. `content-pack-maker#28 <https://github.com/fle-internal/content-pack-maker/issues/28>`__. :url-issue:`5120`

Known issues
^^^^^^^^^^^^

 * Mac OSX installer version (based on pyrun) crashes :url-issue:`5211` - will be fixed in 0.16.8
 * Windows installer tray application option "Run on start" does not work see `learningequality/installers#106 <https://github.com/learningequality/installers/issues/106>`__
 * Learner is not notified of mastery level, exercises keep displaying :url-issue:`4875`
 * Writing to ``server.log`` is disabled on Windows :url-issue:`5057`
 * Exercise "Measure area with unit squares" is broken :url-issue:`5130`
 * VTT Subtitles are broken in Epiphany browser :url-issue:`5125`
 * Viewing subtitles on Ubuntu requires ubuntu-restricted-extras :url-issue:`4993`
 * Individual Student Progress Report may take a long time to load :url-issue:`5106`
 * Button "Show Keypad" may be missing on some exercises due to upstream data API issue :url-issue:`5103`
 * Installing on Windows 8, 32bit is reported to take ~1 hour before eventually finishing.


0.16.6
------

Bug fixes
^^^^^^^^^

 * Content packs updated, bulk of broken exercises fixed and all languages rebuilt (and should be re-downloaded), pay attention to a couple of known issues!
 * Allow logins during LOCKDOWN :url-issue:`5117`
 * Remove RPI warning message about max number of concurrent downloads, there's no longer a limit on small platforms :url-issue:`4982`
 * Make ROOT_DATA_PATH consider the KALITE_DIR environment variable :url-issue:`5143`
 * Restore downloading on RPI w/ m2crypto: Unbundle requests and use requests.get instead of urllib.urlretrieve :url-issue:`5138`
 * Docs: Add warning message on KA Lite windows application docs :url-issue:`5137`
 * Treat socket.error as if no server is running :url-issue:`5135` 
 * Docs: Connect to ka-lite on IRC #ka-lite (Freenode) - :url-issue:`5127`
 * Notify student when all exercises in a series are completed (level has been mastered) :url-issue:`4875`
 * Use current year in parts of footer :url-issue:`5112`
 * Handle socket.error: Fix some cases where KA Lite fails to start due to a previous unclean shutdown :url-issue:`5132`
 * **Content packs** 1800 outdated questions (assessment items) inside exercises (English version) used to cause problems due to their widgets and have been removed - not only by KA Lite, but also on KhanAcademy.org. This does not affect the number of exercises and there are still 29,839 assessment items left, so it's not a big concern! :url-issue:`5131`

Known issues
^^^^^^^^^^^^

Please note that issues with **content packs** are not related to the software
itself but are being fixed and updated along side our release.

Watch individual issues on Github or
`dev@learningequality.org <https://groups.google.com/a/learningequality.org/forum/#!forum/dev>`__
for announcements and updates.

 * **Content packs** ~1700 dubbed videos are missing in Non-English versions of the content packs, making the following languages have empty content databases: Burmese, Indonesian, Kannada, Swahili, Tamil, Xhosa, Zulu. These issues can be tracked in `content-pack-maker#28 <https://github.com/fle-internal/content-pack-maker/issues/28>`__. :url-issue:`5120`
 * Learner is not notified of mastery level, exercises keep displaying :url-issue:`4875`
 * Login counts and session times in Learner progress reports are wrong :url-issue:`5157`
 * Browsers on Windows XP are experiencing issues with SVG images :url-issue:`5140`
 * Exercise "Measure area with unit squares" is broken :url-issue:`5130`
 * VTT Subtitles are broken in Epiphany browser :url-issue:`5125`
 * Viewing subtitles on Ubuntu requires ubuntu-restricted-extras :url-issue:`4993`
 * Individual Student Progress Report may take a long time to load :url-issue:`5106`
 * Button "Show Keypad" may be missing on some exercises due to upstream data API issue :url-issue:`5103`
 * Writing to server.log is disabled on Windows :url-issue:`5057`


0.16.5
------

Bug fixes
^^^^^^^^^

 * Missing fonts for some icons and math symbols :url-issue:`5110`

0.16.4
------

Bug fixes
^^^^^^^^^

 * Update Perseus JS modules resulting in many broken exercises :url-issue:`5105` :url-issue:`5036` :url-issue:`5099`
 * Fix broken unpacking of legacy assessment items zip :url-issue:`5108`

0.16.3
------

Bug fixes
^^^^^^^^^

 * Fix for 'nix based systems with unconventional kernel versioning :url-issue:`5087`

0.16.2
------

Bug fixes
^^^^^^^^^

 * Fix attempt log filtering :url-issue:`5082`


0.16.1
------

Bug fixes
^^^^^^^^^

 * Tweaks to our documentation :url-issue:`5067`
 * Refactor assessment item asking logic in the setup command :url-issue:`5065`
 * Properly copy over docs pages while preserving content pack assets :url-issue:`5074`
      

0.16.0
------

General
^^^^^^^

 * KA Lite is officially supported on OSX 10.11 (El Capitan).
 * We've revamped the language packs into a new format, called content packs.
   This results in significantly faster startup times across the board.
   .. WARNING:: You will have to redownload all your languages to fully support 0.16.
 * We introduced a new beta inline help system. Check this out by going to the Facility management page and clicking "Show me how!"
 * A lot of UI tweaks and bugfixes. KA Lite is now more stable than ever!


0.15.0
------

General
^^^^^^^

Python 2.6 is no longer supported. It *may* still work, but we are no longer actively supporting it.
Other known issues:

* The latest OSX version (EL Capitan) is not yet supported. KA Lite is officially supported on OS X 10.8 - 10.10.
* On OSX, you must restart the server after downloading videos in order for them to be marked as available.
* On all platforms, you must restart the server after downloading a language pack in order to use it.
* You can no longer configure your server using ``local_settings.py``. Instead, custom settings must appear in
  ``settings.py`` in the user's ``.kalite`` directory.


0.14.0
------

General
^^^^^^^
Installation from source (using ``git``) is no longer supported.
If you have previously installed from source, in order to upgrade you must first install KA Lite again in a new location using one of the supported installers.
Then you can migrate your database and content from your old installation to your new one using the command::

    kalite manage setup --git-migrate=/path/to/your/old/installation/ka-lite

You *must* use the ``kalite`` command that comes with your new installation.
The path you should specify is the base project directory -- it should contain the ``kalite`` directory, which should in turn contain the ``database`` directory.
Follow the on-screen prompts to complete the migration. You should then no longer use the old installation, and should consider deleting it.


0.13.0
------

General
^^^^^^^
Interacting with the system through ``kalite/manage.py`` has now been deprecated. Please use the kalite executable under the ``bin/`` folder. Run ``bin/kalite -h`` for more details.

If you are pulling the source from git, you will need to run the setup command to complete the upgrade. From the base directory run::

    bin/kalite manage setup

On Windows, use the ``bin\windows\kalite.bat`` in the cmd.exe prompt::

    bin\windows\kalite.bat manage setup

When you are asked whether or not to delete your database, you should choose to keep your database! You will also be prompted to download an assessment items package, or to specify the location if you have already downloaded it. If you wish to download the package and specify the location during the setup process:

* Download the assessment items package `here <https://learningequality.org/downloads/ka-lite/0.13/content/assessment.zip>`_. Save it in the same folder as the setup script.
* During the setup process you will see the prompt "Do you wish to download the assessment items package now?". Type "no" and press enter to continue.
* You will then see the prompt "Have you already downloaded the assessment items package?". Type "yes" and press enter.
* Finally, you will see a prompt that begins with "Please enter the filename of the assessment items package you have downloaded". A recommened file may appear in parentheses -- if this is the file you downloaded, then press enter. Otherwise, enter the name of the file you downloaded. (Absolute paths are okay, as are paths relative to the directory you are running the setup script from.)

Windows
^^^^^^^
.. WARNING::
    Internet Explorer 8 is no longer supported in this version. Please use a newer browser, or stick to version 0.12 to maintain compatibility.

Raspberry Pi
^^^^^^^^^^^^
If you're updating a current Raspberry Pi installation, make sure to put this in your ``local_settings.py`` to avoid slow performance:

    DO_NOT_RELOAD_CONTENT_CACHE_AT_STARTUP = True
    


Purging \*pyc files
^^^^^^^^^^^^^^^^^^^

Previously, kalite would look for ``*pyc`` files every time it was launched,
and that was quite a waste since its only useful when upgrading. In dev
environments, we recommend that the developer keeps track of these issues
on his/her own as with any other project.

Tips:
http://blog.daniel-watkins.co.uk/2013/02/removing-pyc-files-coda.html

> Luckily, it's pretty easy to fix this in git, using hooks, specifically the
> post-checkout hook. To do that, add the following to .git/hooks/post-checkout, and make the file executable:

::

    #!/bin/bash
    find $(git rev-parse --show-cdup) -name "*.pyc" -delete

For the normal user, reset assured that the upgrade notes contain more
info.


Which version can I upgrade from?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

0.12


Changes in ``scripts/``
^^^^^^^^^^^^^^^^^^^^^^^

The ``scripts/`` directory now has everything OSX-specific in ``mac/``
and Windows stuff in ``win/``.

These scripts are intended to all deprecate sooner down the road as such
platform-specific logic will be maintained in separate distribution projects.

Scripts have been modified to continue to work but you are encouraged to
make your system setup only invoke the `kalite` in the `bin/` directory.


Starting and stopping kalite
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Starting and stopping kalite is now performed from the new command line interface
`kalite`. Examples::

    kalite start  # Starts the server
    kalite stop  # Stops the server
    kalite restart  # Restarts the server
    kalite status  # Returns the current status of kalite, 0=stopped, 1=running
    kalite manage  # A proxy for the manage.py command.
    kalite manage shell  # Gives you a django shell

