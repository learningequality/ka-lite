# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# __init__.py - kaa.distribution module initialization
# -----------------------------------------------------------------------------
# Copyright 2006-2012 Dirk Meyer, Jason Tackaberry
#
# Please see the file AUTHORS for a complete list of authors.
#
# This library is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License version
# 2.1 as published by the Free Software Foundation.
#
# This library is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301 USA
#
# -----------------------------------------------------------------------------

import sys
import distutils.util


def get_build_directory():
    """
    Returns current build-lib directory.
    """
    return "lib.%s-%s" % (distutils.util.get_platform(), sys.version[0:3])
