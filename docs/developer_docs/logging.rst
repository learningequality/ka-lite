Logging
=======

KA Lite application logs are stored in ``~/.kalite/logs/``. When going to daemon
mode using ``kalite start``, all outputs are additionally stored in
``~/.kalite/server.log``, which may contain more crash information for the last
running instance.

In Python, please always log to ``logging.getLogger(__name__)``! Fore more
information on how logging is setup, refer to ``kalite.settings.base.LOGGING``.

If you wish to view output from the server, you have a few options:

*  Start the server with ``kalite start --foreground``. This will start the server using CherryPy and a single thread, with output going to your terminal.
*  Start the server in development mode ``kalite manage runserver --settings=kalite.project.settings.dev`` (this doesn't start the job scheduler).

