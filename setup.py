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

# Since pip 7.0.1, bdist_wheel has started to be called automatically when
# the sdist was being installed. Let's not have that.
# By raising an exception,

if 'bdist_wheel' in sys.argv:
    raise RuntimeError(
        "Harmless: Because of a bug in Wheel, we do not support bdist_wheel. "
        "See: https://bitbucket.org/pypa/wheel/issue/92/bdist_wheel-makes-absolute-data_files"
    )

# Path of setup.py, used to resolve path of requirements.txt file
where_am_i = os.path.dirname(os.path.realpath(__file__))

# Handle requirements
DIST_REQUIREMENTS = open(os.path.join(where_am_i, 'requirements.txt'), 'r').read().split("\n")


def filter_requirement_statements(req):
    """Filter comments and blank lines from a requirements.txt like file
    content to feed pip"""
    # Strip comments and empty lines
    req_pattern = re.compile(r'^\s*([^\#]+)')

    m = req_pattern.search(req)
    if m:
        return m.group(0).replace(" ", "")


# Filter out comments from requirements
DIST_REQUIREMENTS = map(filter_requirement_statements, DIST_REQUIREMENTS)
DIST_REQUIREMENTS = filter(lambda x: bool(x), DIST_REQUIREMENTS)

# Requirements if doing a build with --static
STATIC_REQUIREMENTS = []

# Decide if the invoked command is a request to do building
DIST_BUILDING_COMMAND = any([x in sys.argv for x in ("bdist", "sdist", "bdist_wheel", "bdist_deb", "sdist_dsc")]) and not any([x.startswith("--use-premade-distfile") for x in sys.argv])

# This is where static packages are automatically installed by pip when running
# setup.py sdist --static or if a distributed version built by the static
# installs. This means that "setup.py install" can have two meanings:
#   1. When running from source dir, it means do not install the static version!
#   2. When running from a source built by '--static', it should not install
#      any requirements and instead install all data from dist-packages into
#      where python-packages are going.
STATIC_DIST_PACKAGES = os.path.join(where_am_i, 'dist-packages')

# Create if it doesn't exist in order to avoid warnings from setuptools
if not os.path.exists(STATIC_DIST_PACKAGES):
    os.mkdir(STATIC_DIST_PACKAGES)

# We are running from source if .KALITE_SOURCE_DIR exists
RUNNING_FROM_SOURCE = os.path.exists(os.path.join(where_am_i, ".KALITE_SOURCE_DIR"))

# Default description of the distributed package
DIST_DESCRIPTION = (
    """KA Lite is a light-weight web server for viewing and interacting """
    """with core Khan Academy content (videos and exercises) without """
    """needing an Internet connection."""
)

# This changes when installing the static version
DIST_NAME = 'ka-lite'


# Check if user supplied the special '--static' option
if '--static' in sys.argv:
    sys.argv.remove('--static')
    STATIC_BUILD = True
    DIST_NAME = 'ka-lite-static'
    DIST_DESCRIPTION += " This is the static version, which bundles all dependencies. Recommended for a portable installation method."
    STATIC_REQUIREMENTS = DIST_REQUIREMENTS
    DIST_REQUIREMENTS = []
else:
    STATIC_BUILD = False


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


#############################
# DATA FILES
#############################
# To read more about this, please refer to:
# https://pythonhosted.org/setuptools/setuptools.html#including-data-files
#
# The bundled python-packages are considered data-files because they are
# platform independent and because they are not supposed to live in the general
# site-packages directory.


def gen_data_files(*dirs):
    """
    We can only link files, not directories. Therefore, we use an approach
    that scans all files to pass them to the data_files kwarg for setup().
    Thanks: http://stackoverflow.com/a/7288382/405682
    """
    results = []
    
    filter_illegal_extensions = lambda f: os.path.splitext(f)[1] != ".pyc"
    
    for src_dir in dirs:
        for root, dirs, files in os.walk(src_dir):
            results.append(
                (
                    root,
                    filter(
                        filter_illegal_extensions,
                        map(lambda f: os.path.join(root, f), files)
                    )
                )
            )
    return results

# Append the ROOT_DATA_PATH to all paths
data_files = map(
    lambda x: (os.path.join(kalite.ROOT_DATA_PATH, x[0]), x[1]),
    gen_data_files('python-packages')
)

data_files += map(
    lambda x: (os.path.join(kalite.ROOT_DATA_PATH, x[0]), x[1]),
    gen_data_files('data')
)

data_files += map(
    lambda x: (os.path.join(kalite.ROOT_DATA_PATH, x[0]), x[1]),
    gen_data_files('static-libraries')
)

# For now, just disguise the kalitectl.py script here as it's only to be accessed
# with the bin/kalite proxy.
data_files += [(
    kalite.ROOT_DATA_PATH, [os.path.join(where_am_i, 'kalitectl.py')]
)]


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

# If it's a static build, we invoke pip to bundle dependencies in python-packages
# This would be the case for commands "bdist" and "sdist"
if STATIC_BUILD:
    
    manifest_content = file(os.path.join(where_am_i, 'MANIFEST.in.dist'), 'r').read()
    manifest_content += "\n" + "recursive-include dist-packages *\nrecursive-exclude dist-packages *pyc"
    file(os.path.join(where_am_i, 'MANIFEST.in'), "w").write(manifest_content)
    
    sys.stderr.write(
        "This is a static build... invoking pip to put static dependencies in "
        "dist-packages/\n"
    )
    
    STATIC_DIST_PACKAGES_DOWNLOAD_CACHE = os.path.join(where_am_i, 'dist-packages-downloads')
    STATIC_DIST_PACKAGES_TEMP = os.path.join(where_am_i, 'dist-packages-temp')
    
    # Create directory where dynamically created dependencies are put
    if not os.path.exists(STATIC_DIST_PACKAGES_DOWNLOAD_CACHE):
        os.mkdir(STATIC_DIST_PACKAGES_DOWNLOAD_CACHE)
    
    # Should remove the temporary directory always
    if os.path.exists(STATIC_DIST_PACKAGES_TEMP):
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
        opts.compile = False
        opts.ignore_dependencies = True
        opts.use_wheel = False
        opts.no_clean = False
        command.run(opts, distributions)
        # requirement_set.source_dir = STATIC_DIST_PACKAGES_TEMP
        # requirement_set.install(opts)
    
    # Install requirements into dist-packages
    if DIST_BUILDING_COMMAND:
        install_distributions(STATIC_REQUIREMENTS)
    
    # Empty the requirements.txt file


# It's not a build command with --static or it's not a build command at all
else:
    
    # If the dist-packages directory is non-empty
    if os.listdir(STATIC_DIST_PACKAGES):
        # If we are building something or running from the source
        if DIST_BUILDING_COMMAND or (RUNNING_FROM_SOURCE and "install" in sys.argv):
            sys.stderr.write((
                "Installing from source or not building with --static, so clearing "
                "out dist-packages: {}\n\nIf you wish to install a static version "
                "from the source distribution, use setup.py install --static\n\n"
                "ENTER to continue or CTRL+C to cancel\n\n"
            ).format(STATIC_DIST_PACKAGES))
            sys.stdin.readline()
            shutil.rmtree(STATIC_DIST_PACKAGES)
            os.mkdir(STATIC_DIST_PACKAGES)
        else:
            # There are distributed requirements in dist-packages, so ignore
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
    
    # No dist-packages/ and not building, so must be installing the dynamic
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

    if os.path.exists(os.path.join(where_am_i, 'MANIFEST.in.dist')):
        manifest_content = file(os.path.join(where_am_i, 'MANIFEST.in.dist'), 'r').read()
        manifest_content += "\n" + "recursive-include dist-packages *"
        file(os.path.join(where_am_i, 'MANIFEST.in'), "w").write(manifest_content)
    

# All files from dist-packages are included if the directory exists
if os.listdir(STATIC_DIST_PACKAGES):
    data_files += map(
        lambda x: (os.path.join(kalite.ROOT_DATA_PATH, x[0]), x[1]),
        gen_data_files('dist-packages')
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
    packages=find_packages(exclude=["python-packages"]),
    data_files=data_files,
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
