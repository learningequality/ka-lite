Installation overview
===

You will be completing the following steps:

1. Install Python version 2.6 or 2.7
2. Install git
3. Download the KA Lite codebase using git
4. Run the installation script to complete configuration
5. Run the server

Jump to below for [Windows installation instructions](#installing-on-windows).

Installing on Linux
===

### 1. Install Python

Almost all popular versions of Linux come with Python already installed. To ensure that it is a usable version, run `python -V` from the command line, and ensure that the version number starts with 2.6, or 2.7.

If Python is not installed, install it by running `sudo apt-get install python` or the equivalent command in your distribution's package manager.

### 2. Install git

Install git by running `sudo apt-get install git-core` or the equivalent command in your distribution's package manager.

### 3. Download KA Lite

Clone the repository into a directory of your choice. Use `cd` to navigate into the target directory, and then run the command below (the files will be put into a subdirectory of your current directory named `ka-lite`):

`git clone --recursive https://github.com/jamalex/ka-lite.git`

(The `--recursive` is required because it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule.)

### 4. Run the installation script

Inside the `ka-lite` directory (that you cloned above) you should find a script called `install.sh`. Use `cd ka-lite` to navigate into the directory, and run this script using `./install.sh` to initialize the server database.

### 5. Run the server

(If you're installing the server to test/develop, rather than deploy, follow the [development instructions](docs/DEVELOPMENT.md) instead.)

To start the server, run the `start.sh` script in the `ka-lite` directory.

You may want to have this script run automatically when you start the computer. If you are running Ubuntu or another Debian variant, the installation script should have given you the option of setting the server to run automatically in the background when the computer boots. If you skipped this step, you can do it later by running `sudo ./runatboot.sh` from inside the `ka-lite/kalite` directory.

The local KA Lite website should now be accessible at [http://127.0.0.1:8008/](http://127.0.0.1:8008/) (replace 127.0.0.1 with your computer's external ip address or domain to access it from another connected computer).


Installing on Windows
===

### 1. Install Python

Install Python (version 2.6 or 2.7), if not already installed ([download Python 2.7](http://www.python.org/download/releases/2.7.3/)). On 32-bit Windows, use the [x86 MSI Installer](http://www.python.org/ftp/python/2.7.3/python-2.7.3.msi), and on 64-bit Windows, use the [X86-64 MSI Installer](http://www.python.org/ftp/python/2.7.3/python-2.7.3.amd64.msi).

You will need Python to be on your system PATH, so that it can be run from the command prompt (cmd.exe); see this video about [adding Python to the PATH](http://www.youtube.com/watch?v=ndNlFy-5GKA&hd=1#t=243s) (note that this is for version 2.7; just adapt the paths for older versions). It may be good to add `;C:\Python27\;C:\Python27\Scripts` to your path, instead of just `;C:\Python27\` as recommended in the video.

### 2. Install git

Install the latest version of [git for Windows](http://code.google.com/p/msysgit/downloads/list?q=full+installer+official+git), using all the default options EXCEPT be sure to choose the "Run Git from the Windows Command Prompt" (middle) option on the "Adjusting your PATH environment" page (KA Lite needs to have git accessible on the PATH for updating purposes).

### 3. Download KA Lite

Clone the repository into a folder of your choice. Load `cmd.exe`, and use `cd` to navigate into the target folder (e.g. to put the files in a folder called `ka-lite` on your Desktop, type `cd Desktop`), and then run:

`git clone --recursive https://github.com/jamalex/ka-lite.git`

If you get the message `'git' is not recognized as an internal or external command, operable program or batch file.`, this means git was not added to your PATH. In this case, you can either uninstall git and then re-follow the [git installation instructions above](#2-install-git-1), or [add the git bin folder to your PATH](http://stackoverflow.com/a/4493004/527280) -- use `C:\Program Files\git\bin` (or maybe `C:\Program Files (x86)\git\bin`) as the path.

(The `--recursive` is required because it includes [khan-exercises](https://github.com/Khan/khan-exercises) as a git submodule.)

### 4. Run the installation script

Inside the `ka-lite` folder (that you cloned above) you should find a script called `install.bat`. Use `cd ka-lite` to navigate into the directory, and run this script by typing `install.bat` and pressing Enter, to initialize the server database.

### 5. Run the server

(If you're installing the server to test/develop, rather than deploy, follow the [development instructions](docs/DEVELOPMENT.md) instead.)

To start the server, run the `start.bat` script in the `ka-lite` folder.

You may want to have this script run automatically when you start the computer, by creating a shortcut to `start.bat` and [copying it to the Startup folder in the Start Menu](http://windows.microsoft.com/en-US/windows-vista/Run-a-program-automatically-when-Windows-starts) -- the installation script should also have given you the option of having this done automatically.

If at any point you see a "Windows Security Alert" [warning about Windows Firewall blocking Python](kalite/static/images/windows-python-network-permissions.png), be sure to check both checkboxes (as seen in the picture) and click "Allow access", to ensure that the server will be accessible.

The local KA Lite website should now be accessible at [http://127.0.0.1:8008/](http://127.0.0.1:8008/) (replace 127.0.0.1 with your computer's external ip address or domain to access it from another connected computer).


Optional: Install and configure Apache/mod_wsgi
===

KA Lite includes a web server implemented in pure Python for serving the website, capable of handling hundreds of simultaneous users while using very little memory. However, if for some reason you wish to serve the website through Apache and mod_wsgi, here are some [useful Apache setup tips](docs/INSTALL-APACHE.md).
