# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# core.py - distribution core functions for kaa packages
# -----------------------------------------------------------------------------
# Copyright 2005-2012 Dirk Meyer, Jason Tackaberry
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

# python imports
from __future__ import absolute_import
import os
import sys
import tempfile
import time
import re
import platform
import distutils.core
import distutils.cmd
import distutils.sysconfig
import distutils.dist


# internal imports
from .version import Version
from .build_py import build_py
from .svn2log import svn2log
from .git2log import git2log

__all__ = ['compile', 'check_library', 'get_library', 'setup', 'ConfigFile',
           'Extension', 'Library' ]

_libraries = {}

def compile(includes, code='', args=''):
    fd, outfile = tempfile.mkstemp()
    os.close(fd)
    args += ' %s %s' % (os.getenv('CFLAGS', ''), os.getenv('LDFLAGS', ''))
    cc = os.getenv('CC', 'cc')
    f = os.popen("%s -x c - -o %s %s 2>/dev/null >/dev/null" % (cc, outfile, args), "w")
    if not f:
        return False

    for i in includes:
        f.write('#include %s\n' % i)
    f.write('int main() { ' + code + '\nreturn 0;\n};\n')
    result = f.close()

    if os.path.exists(outfile):
        os.unlink(outfile)

    if result == None:
        return True
    return False


def check_library(name, *args, **kwargs):
    lib = Library(name)
    if len(args) < 2 and not kwargs:
        minver = args[0]
        sys.stdout.write('checking for %s >= %s ...' % (name, minver))
        sys.stdout.flush()
        found, version = lib.check(minver)
        if found:
            print(version)
        elif version:
            print('no (%s)' % version)
            return
        else:
            print('no')
            return
    else:
        for var in ('include_dirs', 'library_dirs', 'libraries'):
            if var in kwargs:
                setattr(lib, var, kwargs.pop(var))
        sys.stdout.write('checking for %s ...' % name)
        sys.stdout.flush()
        if lib.compile(*args, **kwargs):
            print('ok')
        else:
            print('no')
            return
    _libraries[name] = lib
    return lib


def get_library(name):
    lib = _libraries.get(name)
    if lib and lib.valid:
        return lib
    return None


class Library(object):
    def __init__(self, name):
        self.name = name
        self.include_dirs = []
        self.library_dirs = []
        self.libraries = []
        self.version = None
        self.valid = False


    def compare_versions(self, a, b):
        # Get maximum component length in both version.
        maxlen =  max([ len(x) for x in (a + '.' + b).split('.') ])
        # Pad each component of A and B to maxlen
        a = [ x.zfill(maxlen) for x in a.split('.') ]
        b = [ x.zfill(maxlen) for x in b.split('.') ]
        # TODO: special handling of rc and beta (others?) suffixes, so
        # that 1.0.0 > 1.0.0rc1
        return (a > b) - (a < b)


    def get_numeric_version(self, version = None):
        """
        Returns an integer version suitable for numeric comparison.  This
        returns the version of the library gotten after calling check().  If
        check() was not called this method will raise an exception.

        This algorithm is pretty naive and won't work at all if the version
        contains any non-numeric characters.
        """
        if version is None:
            version = self.version

        if version is None:
            raise ValueError('Version is not known; call check() first')

        if not version.replace(".", "").isdigit():
            raise ValueError('Version cannot have non-numeric characters.')

        # Performs: 1.2.3.4 => 4<<0 + 3<<9 + 2<<18 + 1<<27
        return sum([ int(v) << 9*s for s,v in enumerate(reversed(version.split('.'))) ])


    def check(self, minver):
        """
        Check dependencies add add the flags to include_dirs, library_dirs and
        libraries. The basic logic is taken from pygame.
        """
        if os.system("%s-config --version >/dev/null 2>/dev/null" % self.name) == 0:
            # Use foo-config if it exists.
            command = "%s-config %%s 2>/dev/null" % self.name
            version_arg = "--version"
        elif os.system("pkg-config %s --exists >/dev/null 2>/dev/null" % self.name) == 0:
            # Otherwise try pkg-config foo.
            command = "pkg-config %s %%s 2>/dev/null" % self.name
            version_arg = "--modversion"
        else:
            return False, None

        version = os.popen(command % version_arg).read().strip()
        if len(version) == 0:
            return False, None
        if minver and self.compare_versions(minver, version) > 0:
            return False, version

        for inc in os.popen(command % "--cflags").read().strip().split(' '):
            if inc[2:] and not inc[2:] in self.include_dirs:
                self.include_dirs.append(inc[2:])

        for flag in os.popen(command % "--libs").read().strip().split(' '):
            if flag[:2] == '-L' and not flag[2:] in self.library_dirs:
                self.library_dirs.append(flag[2:])
            if flag[:2] == '-l' and not flag[2:] in self.libraries:
                self.libraries.append(flag[2:])

        self.version = version
        self.valid = True
        return True, version


    def compile(self, includes, code='', args='', extra_libraries = []):
        ext_args = [ "-L%s" % x for x in self.library_dirs ] + \
                   [ "-l%s" % x for x in self.libraries ] + \
                   [ "-I%s" % x for x in self.include_dirs ]

        for lib in extra_libraries:
            if isinstance(lib, basestring):
                lib = get_library(lib)
            for dir in lib.library_dirs:
                ext_args.append("-L%s" % dir)
            for dir in lib.include_dirs:
                ext_args.append("-I%s" % dir)

        # FIXME: we do not check if the lib is installed, we only
        # check the header files.
        if compile(includes, code, args + ' %s' % ' '.join(ext_args)):
            self.valid = True
            return True

        return False



class ConfigFile(object):
    """
    Config file for the build process.
    """
    def __init__(self, filename):
        self.file = os.path.abspath(filename)
        # create config file
        open(self.file, 'w').close()


    def append(self, line):
        """
        Append something to the config file.
        """
        f = open(self.file, 'a')
        f.write(line + '\n')
        f.close()


    def define(self, variable, value=None):
        """
        Set a #define.
        """
        if value == None:
            self.append('#define %s' % variable)
        else:
            self.append('#define %s %s' % (variable, value))


    def unlink(self):
        """
        Delete config file.
        """
        os.unlink(self.file)


class Extension(object):
    """
    Extension wrapper with additional functions to find libraries and
    support for config files.
    """
    def __init__(self, output, files, include_dirs=[], library_dirs=[],
                 libraries=[], extra_compile_args = [], config=None):
        """
        Init the Extension object.
        """
        self.output = output
        self.files = files
        self.include_dirs = include_dirs[:]
        self.library_dirs = library_dirs[:]
        self.libraries = libraries[:]
        self.library_objects = []
        self.extra_compile_args = ["-Wall"] + extra_compile_args
        if config:
            self.configfile = ConfigFile(config)
        else:
            self.configfile = None


    def config(self, line):
        """
        Write a line to the config file.
        """
        if not self.configfile:
            raise AttributeError('No config file defined')
        self.configfile.append(line)


    def add_library(self, name):
        """
        """
        lib = get_library(name)
        if lib and lib not in self.library_objects:
            self.library_objects.append(lib)
        return False


    def get_library(self, name):
        for lib in self.library_objects:
            if lib.name == name:
                return lib


    def check_library(self, name, minver):
        """
        Check dependencies add add the flags to include_dirs, library_dirs and
        libraries. The basic logic is taken from pygame.
        """
        try:
            lib = Library(name)
            found, version = lib.check(minver)
            if not found:
                if not version:
                    version = 'none'
                raise ValueError('requires %s version %s (none found)' % (name, minver, version))
            self.library_objects.append(lib)
            return True
        except Exception:
            # Access exception object from sys.exc_info() so we're compatible with
            # both Python 2.5+ and 3.
            self.error = sys.exc_info()[1]

        return False


    def check_cc(self, includes, code='', args='', extra_libraries = []):
        """
        Check the given code with the linker. The optional parameter args
        can contain additional command line options like -l.
        """
        ext_args = []
        for lib in self.library_objects + extra_libraries:
            for dir in lib.library_dirs:
                ext_args.append("-L%s" % dir)
            for dir in lib.include_dirs:
                ext_args.append("-I%s" % dir)
        args += ' %s' % ' '.join(ext_args)
        return compile(includes, code, args)


    def has_python_h(self):
        """
        Return True if Python.h is found in the system. If not compiling
        the extention will fail in most cases.
        """
        return os.path.exists(os.path.join(distutils.sysconfig.get_python_inc(), 'Python.h'))


    def convert(self):
        """
        Convert Extension into a distutils.core.Extension.
        """
        library_dirs = self.library_dirs[:]
        include_dirs = self.include_dirs[:]
        libraries = self.libraries[:]
        for lib in self.library_objects:
            library_dirs.extend(lib.library_dirs)
            include_dirs.extend(lib.include_dirs)
            libraries.extend(lib.libraries)

        ext = distutils.core.Extension(self.output, self.files,
                                       library_dirs=library_dirs,
                                       include_dirs=include_dirs,
                                       libraries=libraries,
                                       extra_compile_args=self.extra_compile_args)

        # Keep a reference to self in the distutils Extension object, so that
        # after distutils.setup() is run, we can clean() the kaa Extension
        # object.
        ext._kaa_ext = self
        return ext


    def clean(self):
        """
        Delete the config file.
        """
        if self.configfile:
            self.configfile.unlink()


class EmptyExtensionsList(list):
    """
    A list that is non-zero even when empty.  Used for the ext_modules
    kwarg in setup() for modules with no ext_modules.

    This is a kludge to solve a peculiar problem.  On architectures like
    x86_64, distutils will install "pure" modules (i.e. no C extensions)
    under /usr/lib, and platform-specific modules (with extensions) under
    /usr/lib64.  This is a problem for kaa, because with kaa we have a single
    namespace (kaa/) that have several independent modules: that is, each
    module in Kaa can be installed separately, but they coexist under the
    kaa/ directory hierarchy.

    On x86_64, this results in some kaa modules being installed in /usr/lib
    and others installed in /usr/lib64.  The first problem is that
    kaa/__init__.py is provided by kaa.base, so if kaa.base is installed
    in /usr/lib/ then /usr/lib64/python*/site-packages/kaa/__init__.py does
    not exist and therefore we can't import any modules from that.  We could
    drop a dummy __init__.py there, but then python will have two valid kaa
    modules and only ever see one of them, the other will be ignored.

    So this kludge makes distutils always think the module has extensions,
    so it will install in the platform-specific libdir.  As a result, on
    x86_64, all kaa modules will be installed in /usr/lib64, which is what
    we want.
    """
    def __nonzero__(self):
        # Python 2
        return True

    def __bool__(self):
        # Python 3
        return True


class Doc(distutils.cmd.Command):
    """
    Epydoc support
    """
    description = 'generate kaa documentation'
    user_options = []
    docfiles = []

    def initialize_options (self):
        pass

    def finalize_options (self):
        pass

    def run(self):
        self.run_command('build')
        for doc in self.docfiles:
            os.system('epydoc --config=%s' % doc)
        if os.path.isfile('doc/Makefile'):
            os.system('cd doc && make html')


def setup(**kwargs):
    """
    A setup script wrapper for kaa modules.
    """
    def _find_packages(kwargs, prefix):
        """
        Helper function to create 'packages' and 'package_dir'.
        """
        for dirpath, dirnames, files in os.walk('src'):
            for key, value in kwargs.get('plugins', {}).items():
                if dirpath.startswith(value):
                    python_dirpath = key + dirpath[len(value):].replace('/', '.')
                    break
            else:
                python_dirpath = prefix + dirpath[3:].replace('/', '.')
                # Anything under module/src/extensions/foo gets translated to
                # kaa.module.foo.
                python_dirpath = python_dirpath.replace(".extensions.", ".")
            if '__init__.py' in files or python_dirpath.endswith('plugins'):
                kwargs['package_dir'][python_dirpath] = dirpath
                kwargs['packages'].append(python_dirpath)


    if 'module' not in kwargs and 'name' not in kwargs:
        raise AttributeError("'module' not defined")

    # Use setuptools if --egg was passed.  We don't use setuptools by default (yet?)
    # because it changes certain behaviours (like install --prefix=[...]).
    if '--egg' in sys.argv or 'egg_info' in sys.argv:
        try:
            sys.argv.remove('--egg')
        except ValueError:
            pass
        import setuptools

    # Add --egg option
    opt = ('egg', None, "Install with setuptools (use eggs)")
    distutils.dist.Distribution.global_options.append(opt)

    # Handle plugin kwargs; setuptools uses entry_points, but without setuptools
    # we use our custom 'plugins' kwarg.  Both are mandatory for kaa sub-modules.
    plugin_args = kwargs.get('plugins'), kwargs.get('entry_points')
    if plugin_args != (None, None):
        if None in plugin_args:
            raise ValueError('For plugins, both "plugins" and "entry_points" kwargs are required')
        del kwargs['plugins' if sys.modules.get('setuptools') else 'entry_points']

    if not sys.modules.get('setuptools'):
        # Setuptools not available, so remove any kwarg that would cause stock
        # distutils to complain.
        for kw in ('namespace_packages', 'zip_safe', 'install_requires'):
            if kw in kwargs:
                del kwargs[kw]
    else:
        # Setup tools is available on this system.
        if 'zip_safe' not in kwargs:
            # zip_safe not specifically specified, so override the setuptools
            # default and set it to False.  Zipped eggs have a number of problems:
            # http://bugs.python.org/setuptools/issue33
            kwargs['zip_safe'] = False

    # run the distutils.setup function
    project = kwargs.pop('project', 'kaa')

    # create name
    if not 'name' in kwargs:
        kwargs['name'] = project + '-' + kwargs['module']

    # search for source files and add it package_dir and packages
    kwargs['package_dir'] = {}
    kwargs['packages']    = []
    prefix = project + '.' + kwargs['module'] if kwargs.get('module') else kwargs['name']
    _find_packages(kwargs, prefix)

    if 'plugins' in kwargs:
        del kwargs['plugins']

    # convert Extensions
    if kwargs.get('ext_modules'):
        kaa_ext_modules = kwargs['ext_modules']
        ext_modules = []
        for ext in kaa_ext_modules:
            ext_modules.append(ext.convert())
        kwargs['ext_modules'] = ext_modules
        # We need to compile an extension, so first do a naive check to ensure
        # Python headers are available.
        if not os.path.exists(os.path.join(distutils.sysconfig.get_python_inc(), 'Python.h')):
            print('- Python headers not found; please install python development package.')
            sys.exit(1)

    else:
        # No extensions, but trick distutils into thinking we do have, so
        # the module gets installed in the platform-specific libdir.
        kwargs['ext_modules'] = EmptyExtensionsList()

    # check version.py information
    write_version = False
    if 'version' in kwargs:
        write_version = True
        # check if a version.py is there
        if os.path.isfile('src/version.py'):
            # read the file to find the old version information
            f = open('src/version.py')
            for line in f.readlines():
                m = re.search(r'Version\((.*?)\)', line)
                if m and m.group(1).strip('"\'') == kwargs['version']:
                    write_version = False
                    break
            f.close()

    auto_changelog = kwargs.pop('auto_changelog', False)
    if any(arg.startswith('bdist') or arg.startswith('sdist') for arg in sys.argv):
        if auto_changelog:
            if os.path.isdir('.git'):
                print('generate ChangeLog from git')
                git2log()
            elif os.path.isdir('.svn'):
                print('generate ChangeLog from svn')
                svn2log(kwargs.get('module', kwargs.get('name')))

        if os.path.isfile('doc/Makefile'):
            # FIXME: this does not work in some cases. Sphinx requires the
            # files in build to generate the doc files. The build directory
            # itself is not required for sdist.
            print('generate doc')
            os.system('(cd doc; make clean; make html)')

    # delete 'module' information, not used by distutils.setup
    kwargs.pop('module', None)

    # Write a version.py and add it to the list of files to
    # be installed.
    if write_version:
        f = open('src/version.py', 'w')
        f.write('# version information for %s\n' % kwargs['name'])
        f.write('# autogenerated by kaa.distribution\n\n')
        f.write('from kaa.base.distribution.version import Version\n')
        f.write('VERSION = __version__ = Version(\'%s\')\n' % kwargs['version'])
        f.close()

    # add some missing keywords
    if 'author' not in kwargs:
        kwargs['author'] = 'Freevo Development Team'
    if 'author_email' not in kwargs:
        kwargs['author_email'] = 'freevo-devel@lists.sourceforge.net'
    if 'url' not in kwargs:
        kwargs['url'] = 'http://freevo.org/kaa/'

    # We use summary and description as keywords that map to distutils
    # description and long_description
    if 'description' in kwargs:
        kwargs['long_description'] = kwargs['description']
        del kwargs['description']
    if 'summary' in kwargs:
        kwargs['description'] = kwargs['summary']
        if 'long_description' not in kwargs:
            kwargs['long_description'] = kwargs['summary']
        del kwargs['summary']

    # add extra commands
    if 'cmdclass' not in kwargs:
        kwargs['cmdclass'] = {}
    kwargs['cmdclass']['build_py'] = build_py

    kwargs['cmdclass']['doc'] = Doc
    Doc.docfiles = kwargs.pop('epydoc', [])

    if len(sys.argv) > 1 and sys.argv[1] == 'bdist_rpm':
        dist = None
        kwargs['name'] = 'python-' + kwargs['name']
        release = "1"
        if '--dist' in sys.argv:
            # TODO: determine this automatically
            idx = sys.argv.index('--dist')
            sys.argv.pop(idx)
            dist = sys.argv.pop(idx)

        if '--release' in sys.argv:
            idx = sys.argv.index('--release')
            sys.argv.pop(idx)
            release = sys.argv.pop(idx)

        if '--snapshot' in sys.argv:
            # If --snapshot is specified on the command line, set the release
            # to contain today's date, for bundling svn snapshots.
            release = "0.%s" % time.strftime("%Y%m%d")
            sys.argv.remove('--snapshot')

        if dist:
            release += "." + dist

        sys.argv.append('--release=%s' % release)

        if 'rpminfo' in kwargs:
            # Grab rpm metadata from setup kwargs and expose as cmdline
            # parameters to distutils.
            rpminfo = kwargs['rpminfo']
            if dist in rpminfo:
                # dist-specific parameters take precedence
                for key, value in rpminfo[dist].items():
                    rpminfo[key] = value
            for param in ('requires', 'build_requires', 'conflicts', 'obsoletes', 'provides'):
                if param in rpminfo:
                    sys.argv.append("--%s=%s" % (param.replace('_', '-'), rpminfo[param]))


    if 'rpminfo' in kwargs:
        del kwargs['rpminfo']

    # run the distutils.setup function
    if 'opts_2to3' in kwargs:
        build_py.opts_2to3 = kwargs['opts_2to3']
        del kwargs['opts_2to3']

    distutils.core.setup(**kwargs)

    # Run cleanup on extensions (for example to delete config.h)
    for ext in kwargs['ext_modules']:
        ext._kaa_ext.clean()
