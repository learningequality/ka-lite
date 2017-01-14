The ``kalite`` command
======================

Once installed, a new command ``kalite`` is available from your terminal:

.. code-block:: bash

  # Start the server in the background (as a daemon)
  kalite start

  # Stop the server
  kalite stop

  # Stop and start the server in the background (as a daemon)
  kalite restart

  # Runs a foreground process where you can see output of the server
  kalite start --foreground

  # Show available commands
  kalite manage help


.. warning::

  On Ubuntu/Debian/RaspberryPi, when installed via a .deb package, you should start and stop your server with system commands ``sudo service ka-lite start/stop/restart``. The reason is that kalite runs with a configured user account.
  
  Using the package ``ka-lite-raspberry-pi``, it runs on a different port.
  
  These configurations will not be active if you run a ``kalite`` command from your own command line.


.. automodule:: kalite.cli
  :undoc-members:
  :show-inheritance:
