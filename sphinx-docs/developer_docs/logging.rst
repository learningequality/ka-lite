Logging
=======

If you wish to view output from the server, you have a few options:

*  Start the server using the command `kalite manage kaserve --production`.
   This will start the server using CherryPy and a single thread, with output going to stdout and stderr.
*  If you wish to capture the output from `kalite start`, then you need to do two thing:

   *  Opt-in by setting the value of the environment variable NAIVE_LOGGING to "True".
      It is opt-in because there is no rotation or control on log file size.
   *  Ensure that you have write permissions in the directory pointed to by the environment variable KALITE_HOME.
      The output will be logged to the file KALITE_HOME/kalite.log.