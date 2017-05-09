#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
import os
import re
import logging
import pkg_resources
import shutil
import sys

from distutils import log
from setuptools import setup, find_packages
from setuptools.command.install_scripts import install_scripts

import kalite

try:
    # There's an issue on the OSX build server -- sys.stdout and sys.stderr are non-blocking by default,
    # which can result in IOError: [Errno 35] Resource temporarily unavailable
    # See similar issue here: http://trac.edgewall.org/ticket/2066#comment:1
    # So we just make them blocking.
    import fcntl

    def make_blocking(fd):
        """
        Takes a file descriptor, fd, and checks its flags. Unsets O_NONBLOCK if it's set.
        This makes the file blocking, so that there are no race conditions if several threads try to access it at once.
        """
        flags = fcntl.fcntl(fd, fcntl.F_GETFL)
        if flags & os.O_NONBLOCK:
            sys.stderr.write("Setting to blocking...\n")
            fcntl.fcntl(fd, fcntl.F_SETFL, flags & ~os.O_NONBLOCK)
        else:
            sys.stderr.write("Already blocking...\n")
        sys.stderr.flush()

    make_blocking(sys.stdout.fileno())
    make_blocking(sys.stderr.fileno())
except ImportError:
    pass


# Since pip 7.0.1, bdist_wheel has started to be called automatically when
# the sdist was being installed. Let's not have that.
# The problem is that it will build a 'ka-lite-static' and call it 'ka-lite'

if 'bdist_wheel' in sys.argv and '-d' in sys.argv:
    open("/tmp/kalite.pip.log", "w").write(str(sys.argv) + "\n" + str(os.environ))
    raise RuntimeError(
        "Harmless: We don't support auto-converting to .whl format. Please "
        "fetch the .whl instead of the tarball."
    )

# Path of setup.py, used to resolve path of requirements.txt file
where_am_i = os.path.dirname(os.path.realpath(__file__))

# Handle requirements
RAW_REQUIREMENTS = open(os.path.join(where_am_i, 'requirements.txt'), 'r').read().split("\n")


def filter_requirement_statements(req):
    """Filter comments and blank lines from a requirements.txt like file
    content to feed pip"""
    # Strip comments and empty lines, but '#' is allowed in a URL!
    if req.startswith('http'):
        return req
    req_pattern = re.compile(r'^(\s*)([^\#]+)')

    m = req_pattern.search(req)
    if m:
        return m.group(0).replace(" ", "")


# Filter out comments from requirements
RAW_REQUIREMENTS = map(filter_requirement_statements, RAW_REQUIREMENTS)
RAW_REQUIREMENTS = filter(lambda x: bool(x), RAW_REQUIREMENTS)

# Special parser for http://blah#egg=asdasd-1.2.3
DIST_REQUIREMENTS = []
for req in RAW_REQUIREMENTS:
    DIST_REQUIREMENTS.append(req)

# Requirements if doing a build with --static
STATIC_REQUIREMENTS = []

# Decide if the invoked command is a request to do building
DIST_BUILDING_COMMAND = any([x in sys.argv for x in ("bdist", "sdist", "bdist_wheel", "bdist_deb", "sdist_dsc")]) and not any([x.startswith("--use-premade-distfile") for x in sys.argv])

# This is where static packages are automatically installed by pip when running
# setup.py sdist --static or if a distributed version built by the static
# installs. This means that "setup.py install" can have two meanings:
#   1. When running from source dir, it means do not install the static version!
#   2. When running from a source built by '--static', it should not install
#      any requirements and instead install all requirements into
#      kalite/packages/dist
STATIC_DIST_PACKAGES = os.path.join(where_am_i, 'kalite', 'packages', 'dist')

# Default description of the distributed package
DIST_DESCRIPTION = (
    """KA Lite is a light-weight web server for viewing and interacting """
    """with core Khan Academy content (videos and exercises) without """
    """needing an Internet connection."""
)

# This changes when installing the static version
DIST_NAME = 'ka-lite'

STATIC_BUILD = False  # Download all dependencies to kalite/packages/dist
NO_CLEAN = False  # Do not clean kalite/packages/dist

# Check if user supplied the special '--static' option
if '--static' in sys.argv:
    sys.argv.remove('--static')
    STATIC_BUILD = True
    if '--no-clean' in sys.argv:
        NO_CLEAN = True
        sys.argv.remove('--no-clean')
    DIST_NAME = 'ka-lite-static'
    DIST_DESCRIPTION += " This is the static version, which bundles all dependencies. Recommended for a portable installation method."
    STATIC_REQUIREMENTS = DIST_REQUIREMENTS
    DIST_REQUIREMENTS = []


def enable_log_to_stdout(logname):
    """Given a log name, outputs > INFO to stdout."""
    log = logging.getLogger(logname)
    log.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    # create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # add formatter to ch
    ch.setFormatter(formatter)
    # add ch to logger
    log.addHandler(ch)


def get_installed_packages():
    """Avoid depending on pip for this task"""
    return [x.key for x in filter(lambda y: where_am_i not in y.location, pkg_resources.working_set)]


if DIST_BUILDING_COMMAND and not os.path.exists(os.path.join(where_am_i, "kalite", "static-libraries", "docs")):
    raise RuntimeError("Not building - kalite/static-libraries/docs not found.")


################
# Windows code #
################
#
# Close your eyes

BAT_TEMPLATE = \
    r"""@echo off
set mypath=%~dp0
set pyscript="%mypath%{FNAME}"
set /p line1=<%pyscript%
if "%line1:~0,2%" == "#!" (goto :goodstart)
echo First line of %pyscript% does not start with "#!"
exit /b 1
:goodstart
set py_exe=%line1:~2%
call %py_exe% %pyscript% %*
"""


class my_install_scripts(install_scripts):
    def run(self):
        install_scripts.run(self)
        if not os.name == "nt":
            return
        for filepath in self.get_outputs():
            # If we can find an executable name in the #! top line of the script
            # file, make .bat wrapper for script.
            with open(filepath, 'rt') as fobj:
                first_line = fobj.readline()
            if not (first_line.startswith('#!') and
                    'python' in first_line.lower()):
                log.info("No #!python executable found, skipping .bat wrapper")
                continue
            pth, fname = os.path.split(filepath)
            froot, ___ = os.path.splitext(fname)
            bat_file = os.path.join(pth, froot + '.bat')
            bat_contents = BAT_TEMPLATE.replace('{FNAME}', fname)
            log.info("Making %s wrapper for %s" % (bat_file, filepath))
            if self.dry_run:
                continue
            with open(bat_file, 'wt') as fobj:
                fobj.write(bat_contents)


# You can open your eyes again
#
#####################
# END: Windows code #
#####################


######################################
# STATIC AND DYNAMIC BUILD SPECIFICS #
######################################

# If it's a static build, we invoke pip to bundle dependencies in kalite/packages/dist
# This would be the case for commands "bdist" and "sdist"
if STATIC_BUILD:

    sys.stderr.write(
        "This is a static build... invoking pip to put static dependencies in "
        "kalite/packages/dist/\n"
    )

    STATIC_DIST_PACKAGES_DOWNLOAD_CACHE = os.path.join(where_am_i, '.pip-downloads')
    STATIC_DIST_PACKAGES_TEMP = os.path.join(where_am_i, '.pip-temp')

    # Create directory where dynamically created dependencies are put
    if not os.path.exists(STATIC_DIST_PACKAGES_DOWNLOAD_CACHE):
        os.mkdir(STATIC_DIST_PACKAGES_DOWNLOAD_CACHE)

    # Should remove the temporary directory always
    if not NO_CLEAN and os.path.exists(STATIC_DIST_PACKAGES_TEMP):
        print("Removing previous temporary sources for pip {}".format(STATIC_DIST_PACKAGES_TEMP))
        shutil.rmtree(STATIC_DIST_PACKAGES_TEMP)

    # Install from pip

    # Code modified from this example:
    # http://threebean.org/blog/2011/06/06/installing-from-pip-inside-python-or-a-simple-pip-api/
    import pip.commands.install

    # Ensure we get output from pip
    enable_log_to_stdout('pip.commands.install')

    def install_distributions(distributions):
        command = pip.commands.install.InstallCommand()
        opts, ___ = command.parser.parse_args([])
        opts.target_dir = STATIC_DIST_PACKAGES
        opts.build_dir = STATIC_DIST_PACKAGES_TEMP
        opts.download_cache = STATIC_DIST_PACKAGES_DOWNLOAD_CACHE
        opts.isolated = True
        opts.ignore_installed = True
        opts.compile = False
        opts.ignore_dependencies = False
        # This is deprecated and will disappear in Pip 10
        opts.use_wheel = False
        # The below is not an option, then we skip mimeparse
        # opts.no_binary = ':all:'  # Do not use any binary files (whl)
        opts.no_clean = NO_CLEAN
        command.run(opts, distributions)

    # Install requirements into kalite/packages/dist
    if DIST_BUILDING_COMMAND:
        install_distributions(RAW_REQUIREMENTS)

        # Now remove Django because it's bundled. It gets installed as an egg
        # so unfortunately, the path is a bit dependent on the specific
        # version installed (we pinned it for reliability in requirements.txt)
        shutil.rmtree(
            os.path.join(STATIC_DIST_PACKAGES, "Django-1.5.12-py2.7.egg-info"),
        )

# It's not a build command with --static or it's not a build command at all
else:

    # If the kalite/packages/dist directory is non-empty
    # Not empty = more than the __init__.py file
    if len(os.listdir(STATIC_DIST_PACKAGES)) > 1:
        # If we are building something or running from the source
        if DIST_BUILDING_COMMAND:
            sys.stderr.write((
                "Installing from source or not building with --static, so clearing "
                "out: {}\n\nIf you wish to install a static version "
                "from the source distribution, use setup.py install --static\n\n"
                "ENTER to continue or CTRL+C to cancel\n\n"
            ).format(STATIC_DIST_PACKAGES))
            sys.stdin.readline()
            shutil.rmtree(STATIC_DIST_PACKAGES)
            os.mkdir(STATIC_DIST_PACKAGES)
            open(os.path.join(STATIC_DIST_PACKAGES, '__init__.py'), "w").write("\n")
        else:
            # There are distributed requirements in kalite/packages, so ignore
            # everything in the requirements.txt file
            DIST_REQUIREMENTS = []
            DIST_NAME = 'ka-lite-static'

            if "ka-lite" in get_installed_packages():
                raise RuntimeError(
                    "Already installed ka-lite so cannot install ka-lite-static. "
                    "Remove existing ka-lite-static packages, for instance using \n"
                    "\n"
                    "    pip uninstall ka-lite-static  # Standard\n"
                    "    sudo apt-get remove ka-lite  # Ubuntu/Debian\n"
                    "\n"
                    "...or other possible installation mechanisms you may have "
                    "been using."
                )

    # No kalite/packages/dist/ and not building, so must be installing the dynamic
    # version
    elif not DIST_BUILDING_COMMAND:
        # Check that static version is not already installed
        if "ka-lite-static" in get_installed_packages():
                raise RuntimeError(
                    "Already installed ka-lite-static so cannot install ka-lite. "
                    "Remove existing ka-lite-static packages, for instance using \n"
                    "\n"
                    "    pip uninstall ka-lite  # Standard\n"
                    "    sudo apt-get remove ka-lite  # Ubuntu/Debian\n"
                    "\n"
                    "...or other possible installation mechanisms you may have "
                    "been using."
                )

setup(
    name=DIST_NAME,
    version=kalite.VERSION,
    author="Foundation for Learning Equality",
    author_email="info@learningequality.org",
    url="https://www.learningequality.org",
    description=DIST_DESCRIPTION,
    license="MIT",
    keywords=("khan academy", "offline", "education", "OER"),
    scripts=['bin/kalite'],
    packages=find_packages(),
    zip_safe=False,
    install_requires=DIST_REQUIREMENTS,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    include_package_data=True,
    cmdclass={
        'install_scripts': my_install_scripts  # Windows bat wrapper
    }
)
