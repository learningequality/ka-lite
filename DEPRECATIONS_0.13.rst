Deprecations in kalite 0.13
===========================

Why in RST, reStructuredText? Because our future sphinx will run on RST.

This is a working copy for making notes on deprecations until the documentation
structure is here.

Purging *pyc files
------------------

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

TODO: Check that a git pull from an older release does not leave behind any
problematic *pyc files and possibly dump this whole thing.

Which version can I upgrade from?
---------------------------------

benjaoming: Certainly not 0.9 since I've removed the line that moves content files.


Changes in scripts/
-------------------

The ``scripts/`` directory now has everything OSX-specific in ``mac/``
and Windows stuff in ``win/``.

These scripts are intended to all deprecate sooner down the road as such
platform-specific logic will be maintained in separate distribution projects.

Scripts have been modified to continue to work but you are encouraged to
make your system setup only invoke the `kalite` in the `bin/` directory.


Starting and stopping kalite
----------------------------

Starting and stopping kalite is now performed from the new command line interface
`kalite`. Examples::

    kalite start  # Starts the server
    kalite stop  # Stops the server
    kalite restart  # Restarts the server
    kalite status  # Returns the current status of kalite, 0=stopped, 1=running
    kalite manage  # A proxy for the manage.py command.
    kalite manage shell  # Gives you a django shell

