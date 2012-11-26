Optional: Install and configure Apache/mod_wsgi
===

KA Lite includes a web server implemented in pure Python for serving the website (see the [main installation docs for instructions](../INSTALL.md) on getting it set up), capable of handling hundreds of simultaneous users while using very little memory. However, if for some reason you wish to serve the website through Apache and mod_wsgi, here are some useful tips.

You will need to install:
* [Apache server](http://httpd.apache.org/) 2.0 or greater (1.3 may also work, but is not tested)
* The [mod_wsgi](http://code.google.com/p/modwsgi/) module for Apache

To get the recommended virtual host settings, run `python manage.py apacheconfig` and copy the output into your Apache config.

### Linux

Most versions of Linux should have Apache available for installation through their package management systems. In Ubuntu/Debian, you should be able to install Apache and mod_wsgi via:

`sudo apt-get install apache2 libapache2-mod-wsgi`

Otherwise, view instructions and installation packages [for other Linux distributions](http://code.google.com/p/modwsgi/wiki/InstallationOnLinux).

### Windows

Install and configure Apache 2.0, 2.2, or 2.4 by following the instructions [here](http://httpd.apache.org/docs/2.2/platform/windows.html).

To add the mod_wsgi plugin to Apache, download the appropriate mod_wsgi file from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi), and copy the file to your Apache modules folder as described [here](http://code.google.com/p/modwsgi/wiki/InstallationOnWindows).

Finally, add this line to httpd.conf file: `LoadModule wsgi_module modules/mod_wsgi.so`

