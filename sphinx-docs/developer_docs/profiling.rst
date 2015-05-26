Profiling KA Lite
=================

Getting a general overview of resources used
--------------------------------------------

To get a sense of the resources used by KA Lite over a period of time,
run the `kalite` command with the `PROFILE` environment variable::

  PROFILE=yes kalite <command>

Upon normal exit, the program will write to a file called
`memory_profile.log` containing the time and resource utilization. For
now we only log memory usage.
