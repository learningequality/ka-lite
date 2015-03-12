Release Notes
=============

0.13.0
------

Interacting with the system through ``kalite/manage.py`` has now been deprecated. Please use the kalite executable under the ``bin/`` folder. Run ``bin/kalite -h`` for more details.

If you are pulling the source from git, you will need to run the setup command to complete the upgrade. From the base directory run::

    /path/to/python/interpreter bin/kalite manage setup

When you are asked whether or not to delete your database, you should choose to keep your database!

.. WARNING:: 
    Internet Explorer 8 is no longer supported in this version.
