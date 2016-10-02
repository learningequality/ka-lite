Developer Utility Commands
==========================

Django Management Commands
--------------------------

All Django management commands can be run by typing::

    bin/kalite manage <command_name>

in the root directory of the KA Lite project.

``generaterealdata``
--------------------

This function is designed to produce example user data for testing various front end functionality, such as coach reports and content recommendation.

It does take some shortcuts, and will not produce accurate answer data for exercises. This is a Django management command and can be run with the following command::

    kalite manage generaterealdata
