Installation overview - Source distribution
===========================================

The "source distribution" of KA Lite does NOT involve compiling anything (since
it's pure Python). You can install it very easily.

**NB! Since KA Lite 0.14, we are no longer supporting the previous method of
installing via git clone.**

Each stable release ships with an installer for Windows, Mac, and Debian/Ubuntu.
Please refer to the [Installation Guide](https://learningequality.org/docs/installguide/install_main.html)

If you are able to use pip and install conventional python packages from an
online source, then the quickest option to install the latest stable release
of KA Lite is `pip install ka-lite` or `pip install ka-lite-static`.


Uninstalling
------------

You can remove KA Lite (when installed from pip or source distribution) with
`pip uninstall ka-lite` or `pip uninstall ka-lite-static` (static version).


Removing user data
------------------

Downloaded videos and database files are in `~/.kalite`. So navigate to the
home directory of the user who used KA Lite and remove that directory to
potentially reclaim lots of hard drive space.


Static vs. Dynamic version
==========================

Apart from Python itself, KA Lite depends on a couple of python applications,
mainly from the Django ecology. These applications can be installed in two ways:

 - **Dynamic**: That means that they are automatically installed through
   *PIP* as a separate software package accessible to your whole system. This
   is recommended if you run KA Lite and have internet access while installing
   and updating.
 - **Static*: Static means that KA Lite is installed with all the external
   applications bundled in. Use this method if you need to have KA Lite
   installed from offline media or if KA Lite's dependencies are in conflict
   with the system that you install upon.


Virtualenv
----------

You can install KA Lite in its very own separate environment that does not
interfere with other Python software on your machine like this:

    pip install virtualenv virtualenvwrapper
    mkvirtualenv my-kalite-env
    workon my-kalite-env
    pip install ka-lite


Installing through PIP or with setup.py
=======================================

This documentation is preliminary and will be moved and restructured.

For command line users with access to PIP, you can install the following versions of KA Lite:

    pip install ka-lite


Static version
--------------

If you need to run KA Lite with static dependencies bundled and isolated from
the rest of your environment, you can run:

    pip install ka-lite-static


Installing tarballs / zip files with setup.py
---------------------------------------------

You can also fetch a tarball directly from PyPi.


Developers
==========

Developers should consider installing in "editable" mode. That means, create a
git clone and from the git clone source dir (with setup.py), run:

    pip install -e .


Testing installers
------------------

Full range of installation testing possibilities:

 - Straight up setuptools test: `python setup.py install`
 - Straight up setuptools test, static: `python setup.py install --static`
 - Straight up pip test: `pip install .`
 - Straight up pip test, static: N/A, the `--static` option can't be passed through pip.
 - Dynamic tarball testing: `python setup.py sdist --static` + `pip install dist/ka-lite-XXXX.tar.gz`.
   Removal: `pip remove ka-lite`.
 - Static tarball testing: `python setup.py sdist --static` + `pip install dist/ka-lite-static-XXXX.tar.gz`
   Removal: `pip remove ka-lite-static`.

Those testing scenarios should be sufficient, but there may be small differences
encountered that we need to look at once in a while with
`pip install -e` (editable mode) or unzipping a source "ka-lite.XXX.zip" and
run setup.py with setuptools instead of through pip.

**Using `pip install` and `--static`**: Is not possible, so you cannot install
the static version in "editable" mode. This is because pip commands do not
pass our user-defined options to setup.py.


Optional: Install and configure Apache/mod_wsgi
===============================================

KA Lite includes a web server implemented in pure Python for serving the website, capable of handling hundreds of simultaneous users while using very little memory. However, if for some reason you wish to serve the website through Apache and mod_wsgi, here are some [useful Apache setup tips](docs/INSTALL-APACHE.md).

