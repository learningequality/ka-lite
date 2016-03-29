Release Notes
=============

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
