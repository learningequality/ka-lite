Release Notes
=============

0.16.7 (unreleased)
-------------------

Bug fixes
^^^^^^^^^

 * Restore learner stats: Correctly display login count and aggregate login durations (previously uncollected data!) :url-issue:`5157`
 * TODO: Mastery percentage wrongly displayed on learner stats page :url-issue:`5181`
 * **Content packs**: Added ~1700 dubbed videos in Non-English versions of the content packs, populating content databases and thus adding language support for: Burmese, Indonesian, Kannada, Swahili, Tamil, Xhosa, Zulu. `content-pack-maker#28 <https://github.com/fle-internal/content-pack-maker/issues/28>`__. :url-issue:`5120`

Known issues
^^^^^^^^^^^^

 * Learner is not notified of mastery level, exercises keep displaying :url-issue:`4875`
 * Browsers on Windows XP are experiencing issues with SVG images :url-issue:`5140`
 * Exercise "Measure area with unit squares" is broken :url-issue:`5130`
 * VTT Subtitles are broken in Epiphany browser :url-issue:`5125`
 * Viewing subtitles on Ubuntu requires ubuntu-restricted-extras :url-issue:`4993`
 * Individual Student Progress Report may take a long time to load :url-issue:`5106`
 * Button "Show Keypad" may be missing on some exercises due to upstream data API issue :url-issue:`5103`
 * Writing to server.log is disabled on Windows :url-issue:`5057`


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
.. WARNING::
   You will have to redownload all your languages to fully support 0.16.

* We introduced a new beta inline help system. Check this out by going to the
  Facility management page and clicking "Show me how!"
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
