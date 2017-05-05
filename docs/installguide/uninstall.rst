Uninstalling
============

Windows
_______

1. Uninstall KA Lite from the Control Panel.
2. In Windows XP, double-click the "Add or Remove Programs" icon, then choose KA Lite.
3. In later version of Windows, click the "Programs and Features" icon, then choose KA Lite.

Mac OSX
_______

Uninstallation from user interface
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Launch ``KA-Lite`` from your ``Applications`` folder.
2. Click on the app icon at the menu bar.
3. Click on ``Preferences`` in the menu option.
4. Click the ``Uninstall KA Lite`` from the ``Preferences`` tab.
5. A confirmation dialogue will appear, followed by a dialogue asking for your local administrator password. After confirming these steps, KA Lite will be uninstalled.

Uninstallation from command line
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Open Terminal.
2. Type ``bash /Applications/KA-Lite/KA-Lite_Uninstall.tool`` in your Terminal and press Enter.
3. You will be prompted to choose to keep or delete your data folder.
4. Another dialog will appear asking your ``Password``, type your password then click on ``Ok`` button.


Linux: Debian/Ubuntu
____________________

Option 1: Open up **Ubuntu Software Center** and locate the KA Lite package.
Press ``Remove``.

Option 2: Use ``apt-get remove <name of package>``. You have to know which
package you installed, typically this is ``ka-lite`` or ``ka-lite-bundle``.


Installed with pip
__________________

You can remove KA Lite (when installed from pip or source distribution) with
``pip uninstall ka-lite`` or ``pip uninstall ka-lite-static`` (static version).

Removing user data
__________________

Some data (like videos and language packs) are downloaded into a location that
depends on the user running the KA Lite server. Removing that directory can
potentially reclaim lots of hard drive space.

On Windows, the HOME and USERPROFILE registry values will be used if set,
otherwise the combination ``%HOMEDRIVE%%HOMEPATH%`` will be used.
You can check these values from the command prompt using the commands
``echo %HOME%``, ``echo $USERPROFILE%``, etc.
Within that directory, the data is stored in the ``.kalite`` subdirectory.
On most versions of Windows, this is ``C:\Users\YourUsername\.kalite\``.

On Linux, OSX, and other Unix-like systems, downloaded videos and database files are in ``~/.kalite``.
