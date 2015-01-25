# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# version.py - version handling for kaa modules
# -----------------------------------------------------------------------------
# Copyright 2005-2012 Dirk Meyer, Jason Tackaberry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MER-
# CHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA
#
# -----------------------------------------------------------------------------

# python imports
import math
import re

# The following two functions are taken from the setuptools project
# (pkg_resources.py) in order to ensure compatibility with its
# versioning scheme.
#
# Setuptool is written by Phillip J. Eby and released under the PSF or
# ZPL licenses.  PSF is GPL-compatible.
component_re = re.compile(r'(\d+ | [a-z]+ | \.| -)', re.VERBOSE)
replace = {'pre':'c', 'preview':'c', '-':'final-', 'rc':'c', 'dev':'@'}.get

def _parse_parts(s):
    for part in component_re.split(s):
        part = replace(part, part)
        if not part or part == '.':
            continue
        if part[:1] in '0123456789':
            yield part.zfill(8)    # pad for numeric comparison
        else:
            yield '*' + part
    yield '*final'  # ensure that alpha/beta/candidate are before final


def _parse(s):
    s = str(s)  # coerce floats if needed
    parts = []
    for part in _parse_parts(s.lower()):
        if part.startswith('*'):
            if part < '*final':   # remove '-' before a prerelease tag
                while parts and parts[-1] == '*final-':
                    parts.pop()
            # remove trailing zeros from each series of numeric parts
            while parts and parts[-1] == '00000000':
                parts.pop()
        parts.append(part)
    return tuple(parts)


class Version(object):
    """
    Version information for kaa modules.

    Version comparison follows the rules defined by `setuptools
    <http://packages.python.org/distribute/setuptools.html#specifying-your-project-s-version>`_.
    """
    def __init__(self, version):
        """
        Set internal version as string.
        """
        self.version = str(version)

    def __str__(self):
        """
        Convert to string.
        """
        return self.version


    def __repr__(self):
        return str(self)


    def __eq__(self, obj):
        return _parse(self.version) == _parse(obj)


    # Python 2.
    def __cmp__(self, obj):
        a = _parse(self.version)
        b = _parse(obj)
        if a == b:
            return 0
        elif a < b:
            return -1
        else:
            return 1


    # Python 3
    def __lt__(self, obj):
        return _parse(self.version) < _parse(obj)

    def __le__(self, obj):
        return _parse(self.version) < _parse(obj)

    def __gt__(self, obj):
        return _parse(self.version) > _parse(obj)

    def __ge__(self, obj):
        return _parse(self.version) >= _parse(obj)
