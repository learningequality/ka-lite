Installation steps
===

1. Install [Python](http://www.python.org/) version 2.5, 2.6 or 2.7
2. Install [git](http://git-scm.com/)
3. Download the KA Lite codebase using git
4. Run the installation script to complete configuration
5. Run the server

Installing on Linux
===

### 1. Install Python

Almost all popular versions of Linux come with Python already installed. To ensure that it is a usable version, run `python -V` from the command line, and ensure that the version number starts with 2.5, 2.6, or 2.7.

If Python is not installed, install it by running `sudo apt-get install python` or the equivalent command in your distribution's package manager.

### 2. Install git

Install git by running `sudo apt-get install git-core` or the equivalent command in your distribution's package manager.

### 3. Download KA Lite

Clone the repository into a directory of your choice. As it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule, you will need to do a recursive clone, i.e.:

`git clone --recursive https://github.com/jamalex/ka-lite.git`

(this will put the project code in a subdirectory of your current directory, named `ka-lite`)

### 4. Run the installation script

Inside the `ka-lite` directory (that you cloned above) you should find a script called `install.sh`. Run this script to initialize the server database.

### 5. Run the server

To start the server, run the `start.sh` script in the `ka-lite` directory. You may want to have this script run automatically when you start the computer.


Installing on Windows
===

### 1. Install Python

Install Python (version 2.5, 2.6 or 2.7), if not already installed. Python 2.7 can be downloaded [here](http://www.python.org/download/releases/2.7.3/). On 32-bit Windows, use the [x86 MSI Installer](http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi), and on 64-bit Windows, use the [X86-64 MSI Installer](http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi).

You will need Python to be on your system PATH, so that it can be run from the command prompt (cmd.exe); see [this video](http://www.youtube.com/watch?v=ndNlFy-5GKA&hd=1#t=243s) for instructions (note that this is for version 2.7; just adapt the paths for older versions). It may be good to add ";C:\Python27\;C:\Python27\Scripts" to your path, instead of just ";C:\Python27\" as recommended in the video.

### 2. Install git

Install the latest version of [git for Windows](http://code.google.com/p/msysgit/downloads/list?q=full+installer+official+git), using all the default options EXCEPT be sure to choose the "Run Git from the Windows Command Prompt" (middle) option on the "Adjusting your PATH environment" page.

### 3. Download KA Lite

Clone the repository into a folder of your choice. As it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule, you will need to do a recursive clone, i.e. (from cmd.exe):

`git clone --recursive https://github.com/jamalex/ka-lite.git`

### 4. Run the installation script

Inside the `ka-lite` folder (that you cloned above) you should find a script called `install.bat`. Run this script to initialize the server database.

### 5. Run the server

To start the server, run the `start.bat` script in the `ka-lite` folder. You may want to have this script run automatically when you start the computer.


(Optional: Install and configure Apache/mod_wsgi)
===

KA Lite includes a web server implemented in pure Python for serving the website, capable of handling hundreds of simultaneous users while using very little memory. However, if for some reason you wish to serve the website through Apache and mod_wsgi, here are some useful tips.

You will need to install:
* [Apache server](http://httpd.apache.org/) 2.0 or greater (1.3 may also work, but is not tested)
* The [mod_wsgi](http://code.google.com/p/modwsgi/) module for Apache

To get the recommended virtual host settings, run `python manage.py apacheconfig` and copy the output into your Apache config.

### Linux

Most versions of Linux should have Apache available for installation through their package management systems. In Ubuntu/Debian, you should be able to install Apache and mod_esgi via:

`sudo apt-get install apache2 libapache2-mod-wsgi`

Otherwise, view instructions and installation packages [for other Linux distributions](http://code.google.com/p/modwsgi/wiki/InstallationOnLinux).

### Windows

Install and configure Apache 2.0, 2.2, or 2.4 by following the instructions [here](http://httpd.apache.org/docs/2.2/platform/windows.html).

To add the mod_wsgi plugin to Apache, download the appropriate mod_wsgi file from [here](http://www.lfd.uci.edu/~gohlke/pythonlibs/#mod_wsgi), and copy the file to your Apache modules folder as described [here](http://code.google.com/p/modwsgi/wiki/InstallationOnWindows).

Finally, add this line to httpd.conf file: `LoadModule wsgi_module modules/mod_wsgi.so`

