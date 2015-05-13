#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import absolute_import
from __future__ import unicode_literals
import os

import kalite

from setuptools import setup, find_packages


# Handle requirements

requirements = []

# Path of setup.py
where_am_i = os.path.dirname(os.path.realpath(__file__))

requirements += open(os.path.join(where_am_i, 'requirements.txt'), 'r').read().split("\n"),


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

    for src_dir in dirs:
        for root, dirs, files in os.walk(src_dir):
            results.append((root, map(lambda f: os.path.join(root, f), files)))
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

setup(
    name="ka-lite",
    version=kalite.VERSION,
    author="Foundation for Learning Equality",
    author_email="info@learningequality.org",
    url="https://www.learningequality.org",
    description=(
        """KA Lite is a light-weight web server for viewing and interacting """
        """with core Khan Academy content (videos and exercises) without """
        """needing an Internet connection."""
    ),
    license="GPLv3",
    keywords="khan academy offline",
    scripts=['bin/kalite'],
    packages=find_packages(exclude=["python-packages"]),
    data_files=data_files,
    zip_safe=False,
    install_requires=requirements,
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
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
)
