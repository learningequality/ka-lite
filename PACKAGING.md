How we package ka-lite
======================

*April 15, 2015*

Introduction
------------

Our project, ka-lite, was not always intended to be a python package suitable
for PyPi and the likes. However, time has changed that, and we are currently
in the process of making it possible to distribute through traditional
and conventional methods.

Currently, the whole `kalite` package is built for being run on its own and
integrates badly with outside Django environments. The reason for the
stand-alone architecture is the primary intended offline audience, where
external are supposed to be easy to handle. Thus we also package for instance
a stand-alone web server with its own set of python packages. Such external
libraries are added as data files rather than system-wide libraries to avoid
conflicts on the host system imposed by (possibly outdated) KA Lite bundles.

In the future, these bundled dependencies will be cleaned up and integrated
with the upstream such that `kalite` will be available as a conventional
python package with dynamic dependencies and a `standalone` version with
all dependencies statically bundled.


Setuptools vs distutils
-----------------------

It would be really great to be packaging with Python was easy, however it's not.

It's therefore very important to highlight:

**THIS PACKAGING EFFORT IS USING SETUPTOOLS AND NOT DISTUTILS!!!**


Success criteria
----------------

We want all this to work:

 * Everything is installed with `python manage.py install`.
 * Should be installable in a virtualenv <- This means that we can't just put
   files in system-wide directories by default.
 * Furthermore, that a local virtualenv correctly links in a development env
   with `pip install -e .`.
 * Compatible with `stdeb` for converting to a debian package, seemlessly
   with py2dsc.


How package data is found
-------------------------

We use `sys.prefix` to find data files and append fixed configured paths to
the prefix.

This is the best, and furthermore the only way to create paths that are under
the package system's control as we are currently storing non-package related
data.

All of this is achieved by feeding the `setup()` argument `data_files` with
relative paths as described
[in the docs](https://docs.python.org/2/distutils/setupscript.html#installing-additional-files).

Other approaches have been tested, such as MANIFEST.in, but it cannot be
used for these non-package files.
