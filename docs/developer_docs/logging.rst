Logging
=======

If you wish to view output from the server, you have a few options:

*  Start the server with ``kalite start --foreground``. This will start the server using CherryPy and a single thread, with output going to your terminal.
*  Start the server in development mode ``kalite manage runserver --settings=kalite.project.settings.dev`` (this doesn't start the job scheduler).
*  Run the normal mode ``kalite start``, and check ``~/.kalite/server.log`` for output.
