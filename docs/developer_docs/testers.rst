Overview for installation testers
=================================

Here's an overview of the various ways of installing KA Lite as a reference
to testers and package maintainers:

 * The Windows installer
 * The OSX installer
 * .deb packages installed without dependencies: ``dpkg -i package.deb``.
 * Installation from PPA
 * Source code setuptools test: ``python setup.py install``
 * Source code setuptools test, static: ``python setup.py install --static``
 * Source code pip test: ``pip install .``
 * Source code pip test, static: N/A, the ``--static`` option can't be passed through pip.
 * Dynamic tarball testing: ``python setup.py sdist --static`` + ``pip install dist/ka-lite-XXXX.tar.gz``.
   * Removal: ``pip remove ka-lite``.
 * Static tarball testing: ``python setup.py sdist --static`` + ``pip install dist/ka-lite-static-XXXX.tar.gz``
   * Removal: ``pip remove ka-lite-static``.
 * Wheel / whl: Not supported in 0.14.

