# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# utils.py - Miscellaneous system utilities
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
from __future__ import absolute_import

__all__ = [
    'tempfile', 'which', 'Lock', 'daemonize', 'is_running', 'set_running',
    'set_process_name', 'get_num_cpus', 'get_machine_uuid', 'get_plugins',
    'Singleton', 'property', 'wraps', 'DecoratorDataStore', ]

import sys
import os
import stat
import time
import imp
import zipimport
import logging
import inspect
import re
import functools
import ctypes, ctypes.util
import socket
from tempfile import mktemp

from .weakref import weakref

# get logging object
log = logging.getLogger('kaa.base.utils')

# create tmp directory for the user
TEMP = '/tmp/kaa-%s' % os.getuid()
if os.environ.get('TMPDIR'):
    TEMP = os.path.join(os.environ['TMPDIR'], 'kaa-%s' % os.getuid())

if not os.path.isdir(TEMP):
    try:
        os.mkdir(TEMP, 0700)
    except OSError:
        # This could happen with bad timing starting several kaa
        # applications at once and the scheduler changes between
        # os.path.isdir and the os.mkdir. So if we have an error here,
        # the directory should already exist now.
        if not os.path.isdir(TEMP):
            raise IOError('Security Error: %s is no directory, aborted' % TEMP)
# temp dir is already there, check permissions
if os.path.islink(TEMP):
    raise IOError('Security Error: %s is a link, aborted' % TEMP)
if stat.S_IMODE(os.stat(TEMP)[stat.ST_MODE]) % 01000 != 0700:
    raise IOError('Security Error: %s has wrong permissions, aborted' % TEMP)
if os.stat(TEMP)[stat.ST_UID] != os.getuid():
    raise IOError('Security Error: %s does not belong to you, aborted' % TEMP)


def tempfile(name, unique=False):
    """
    Return a filename in the secure kaa tmp directory with the given name.
    Name can also be a relative path in the temp directory, directories will
    be created if missing. If unique is set, it will return a unique name based
    on the given name.
    """
    name = os.path.join(TEMP, name)
    if not os.path.isdir(os.path.dirname(name)):
        os.mkdir(os.path.dirname(name))
    if not unique:
        return name
    return mktemp(prefix=os.path.basename(name), dir=os.path.dirname(name))


def which(file, path = None):
    """
    Does what which(1) does: searches the PATH in order for a given file name
    and returns the full path to first match.
    """
    if not path:
        path = os.getenv("PATH")

    for p in path.split(":"):
        fullpath = os.path.join(p, file)
        try:
            st = os.stat(fullpath)
        except OSError:
            continue

        if os.geteuid() == st[stat.ST_UID]:
            mask = stat.S_IXUSR
        elif st[stat.ST_GID] in os.getgroups():
            mask = stat.S_IXGRP
        else:
            mask = stat.S_IXOTH

        if stat.S_IMODE(st[stat.ST_MODE]) & mask:
            return fullpath

    return None


class Lock(object):
    def __init__(self):
        self._read, self._write = os.pipe()

    def release(self, exitcode):
        os.write(self._write, str(exitcode))
        os.close(self._read)
        os.close(self._write)

    def wait(self):
        exitcode = os.read(self._read, 1)
        os.close(self._read)
        os.close(self._write)
        return int(exitcode)

    def ignore(self):
        os.close(self._read)
        os.close(self._write)


# TODO: review http://code.activestate.com/recipes/278731/
def daemonize(stdin=os.devnull, stdout=os.devnull, stderr=None,
              pidfile=None, exit=True, wait=False):
    """
    Does a double-fork to daemonize the current process using the technique
    described at http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16 .

    If exit is True (default), parent exits immediately.  If false, caller will receive
    the pid of the forked child.
    """

    lock = 0
    if wait:
        lock = Lock()

    # First fork.
    try:
        pid = os.fork()
        if pid > 0:
            if wait:
                exitcode = lock.wait()
                if exitcode:
                    sys.exit(exitcode)
            if exit:
                # Exit from the first parent.
                sys.exit(0)

            # Wait for child to fork again (otherwise we have a zombie)
            os.waitpid(pid, 0)
            return pid
    except OSError, e:
        log.error("Initial daemonize fork failed: %d, %s\n", e.errno, e.strerror)
        sys.exit(1)

    os.chdir("/")
    os.setsid()

    # Second fork.
    try:
        pid = os.fork()
        if pid > 0:
            # Exit from the second parent.
            sys.exit(0)
    except OSError, e:
        log.error("Second daemonize fork failed: %d, %s\n", e.errno, e.strerror)
        sys.exit(1)

    # Create new standard file descriptors.
    if not stderr:
        stderr = stdout
    stdin = open(stdin, 'r')
    stdout = open(stdout, 'a+')
    stderr = open(stderr, 'a+', 0)
    if pidfile:
        open(pidfile, 'w+').write("%d\n" % os.getpid())

    # Remap standard fds.
    os.dup2(stdin.fileno(), sys.stdin.fileno())
    os.dup2(stdout.fileno(), sys.stdout.fileno())
    os.dup2(stderr.fileno(), sys.stderr.fileno())

    # Replace any existing thread notifier pipe, otherwise we'll be listening
    # to our parent's thread pipe.
    from . import main
    if main.is_initialized():
        main.init(reset=True)
    return lock


def fork():
    """
    Forks the process.  May safely be called after the main loop has been
    started.
    """
    pid = os.fork()
    if not pid:
        # Child must replace thread notifier pipe, otherwise we'll be listening
        # to our parent's thread pipe.
        from . import main
        if main.is_initialized():
            main.init(reset=True)
    return pid


def is_running(name):
    """
    Check if the program with the given name is running. The program
    must have called set_running itself. Returns the pid or 0.
    """
    if not os.path.isfile(tempfile('run/' + name)):
        return 0
    run = open(tempfile('run/' + name))
    pid = run.readline().strip()
    cmdline = run.readline()
    run.close()
    if not os.path.exists('/proc/%s/cmdline' % pid):
        return 0
    current = open('/proc/%s/cmdline' % pid).readline()
    if current == cmdline or current.strip('\x00') == name:
        return int(pid)
    return 0


def set_running(name, modify = True):
    """
    Set this program as running with the given name.  If modify is True,
    the process name is updated as described in set_process_name().
    """
    cmdline = open('/proc/%s/cmdline' % os.getpid()).readline()
    run = open(tempfile('run/' + name), 'w')
    run.write(str(os.getpid()) + '\n')
    run.write(cmdline)
    run.close()
    if modify:
        set_process_name(name)


def set_process_name(name):
    """
    On Linux systems later than 2.6.9, this function sets the process name as it
    appears in ps, and so that it can be found with killall(1) and pidof(8).

    .. note::
       name will be truncated to the cumulative length of the original process
       name and all its arguments; once updated, passed arguments will no
       longer be visible.

       This function currently only works properly with Python 2.  With Python
       3, the process will be found with killall(1), but ps(1) and pidof(8)
       will not see the new name.
    """
    libc = ctypes.CDLL(ctypes.util.find_library("c"))
    maxsize = len(open('/proc/%s/cmdline' % os.getpid()).readline())
    name0 = name + '\x00'

    # Python 3's Py_GetArgcArgv() does not return the original argv, but rather
    # a wchar_t copy of it, which means we can't use it.
    if sys.hexversion < 0x03000000:
        c_char_pp = ctypes.POINTER(ctypes.c_char_p)
        Py_GetArgcArgv = ctypes.pythonapi.Py_GetArgcArgv
        Py_GetArgcArgv.restype = None
        Py_GetArgcArgv.argtypes = [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(c_char_pp)]

        argc = ctypes.c_int(0)
        argv = c_char_pp()
        Py_GetArgcArgv(argc, argv)

        ctypes.memset(argv.contents, 0, maxsize)
        ctypes.memmove(argv.contents, name0, len(name0))

    libc.prctl(ctypes.c_int(15), ctypes.c_char_p(name0), 0, 0, 0)  # 15 == PR_SET_NAME


def get_num_cpus():
    """
    Returns the number of processors on the system, or raises RuntimeError
    if that value cannot be determined.
    """
    try:
        if sys.platform == 'win32':
            return int(os.environ['NUMBER_OF_PROCESSORS'])
        elif sys.platform == 'darwin':
            return int(os.popen('sysctl -n hw.ncpu').read())
        else:
            return os.sysconf('SC_NPROCESSORS_ONLN')
    except (KeyError, ValueError, OSError, AttributeError):
        pass

    raise RuntimeError('Could not determine number of processors')


def get_machine_uuid():
    """
    Returns a unique (and hopefully persistent) identifier for the current
    machine.

    This function will return the D-Bus UUID if it exists (which should be
    available on modern Linuxes), otherwise it will return the machine's
    hostname.
    """
    # First try libdbus.
    try:
        lib = ctypes.CDLL(ctypes.util.find_library('dbus-1'))
        ptr = lib.dbus_get_local_machine_id()
        uuid = ctypes.c_char_p(ptr).value
        lib.dbus_free(ptr)
        return uuid
    except AttributeError:
        pass

    # Next try to read from filesystem at well known locations.
    for dir in '/var/lib/dbus', '/etc/dbus-1':
        try:
            return open(os.path.join(dir, 'machine-id')).readline().strip()
        except IOError:
            pass

    # No dbus, fallback to hostname.
    return socket.getfqdn()


def get_plugins(group=None, location=None, attr=None, filter=None, scope=None):
    """
    Flexible plugin loader, supporting Python eggs as well as on-disk trees.
    All modules at the specified location or entry point group (for eggs) are
    loaded and returned as a dict mapping plugin names to plugin objects.

    :param group: a setuptools entry point group name (more below)
    :type group: str or None
    :param location: path within which to load plugins.  If a filename is
                     included, it will be stripped, which means you can
                     conveniently pass ``__file__`` here.  Paths inside eggs are
                     also supported.  All modules at the given location will
                     be imported except for ``__init__``.
    :type location: str or None
    :param attr: if specified, this attribute is fetched from all modules loaded
                 from the specified ``location`` and used as the value in the
                 plugin dict; if not specified, the module itself is used as the
                 module.
    :type attr: str or None
    :param filter: an optional callable to which all candidate module names
                   found at ``location`` will be passed. If the filter returns
                   a zero value that module will skipped, otherwise it will be
                   imported; if the filter returns a string, it specifies the
                   name of a module to be imported instead.
    :type filter: callable or None
    :param scope: the global scope to use when importing plugin modules.  If
                  this is not specified, the caller's scope will be used (using
                  stack inspection trickery).  If get_plugins() is being called
                  indirectly, you will need to pass through the value of
                  globals().
    :type scope: dict
    :returns: a dict mapping plugin names to plugin objects.

    If a plugin raises an exception while it is being imported, the value in
    the returned dictionary for that plugin will be the Exception object that
    was raised.

    Plugins can be loaded by one or both of the following methods:
        #. Loading modules from a specified directory location either on-disk
           or inside a zipped egg
        #. Entry point groups offered by setuptools

    Method 1 is the more traditional approach to plugins in Python.  For example,
    you might have a directory structure like::

        module/
            plugins/
                __init__.py
                plugin1.py
                plugin2.py

    There is typically logic inside ``plugins/__init__.py`` to import all other
    files in the same directory (``os.path.dirname(__file__)``).  It can pass
    ``location=__file__`` to ``kaa.utils.get_plugins()`` to do this:

        >>> kaa.utils.get_plugins(location=__file__)
        {'plugin1': <module 'module.plugins.plugin1' from '.../module/plugins/plugin1.py'>, 
         'plugin2': <module 'module.plugins.plugin2' from '.../module/plugins/plugin2.py'>}

    .. note::
       Plugins will be imported relative to the caller's module name.  So if
       the caller is module ``module.plugins``, plugin1 will be imported as
       ``module.plugins.plugin1``.

    This also works when ``plugins/__init__.py`` is inside a zipped egg.
    However, if you reference ``__file__`` as above, setuptools (assuming it's
    available on the system), when it examines the source code during
    installation, will think it's not safe to zip the tree into an egg file,
    and so it will install it as an on-disk directory tree instead.  You can
    override this by passing ``zip_safe=True`` to ``setup()`` in the setup
    script for the application that loads plugins.

    Method 2 is the approach to take when setuptools is available.  Plugin modules
    register themselves with an entry point group name.  For example, a plugin
    module's ``setup.py`` may call ``setup()`` with::

        setup(
            module='myplugin',
            # ...
            plugins = {'someapplication.plugins': 'src/submodule'},
            entry_points = {'someapplication.plugins': 'plugname = myplugin.submodule:SomeClass'},
        )

    When SomeApplication wants to load all registered modules, it can do::

        >>> kaa.utils.get_plugins(group='someapplication.plugins')
        {'plugname': <class myplugin.submodule.SomeClass at 0xdeadbeef>}

    The ``entry_points`` kwarg specified in the plugin module can specify multiple
    plugin names, and ``SomeClass`` could be any python object, as long as it is
    exposed within ``myplugin.submodule``.  For more information on entry
    points, refer to `setuptools documentation
    <http://peak.telecommunity.com/DevCenter/PkgResources#entry-points>`_.

    It is possible and in fact recommended to mix both methods.  (If your
    project makes setuptools a mandatory dependency, then you can use entry
    point groups exclusively.)  If ``group`` is not specified, then it becomes
    impossible for either the application or the plugin to be installed as
    eggs.

    The ``attr`` kwarg makes it more convenient to combine both methods.
    Plugins loaded from entry points will be SomeClass objects.  If (assuming
    now the application is not installed as a zipped egg but rather an on-disk
    source tree) some plugins were installed to the applications source tree,
    while others installed as eggs registered with the entry point group,
    you would want to pull ``SomeClass`` from those modules loaded from
    ``location``.  So::
    
        >>> kaa.utils.get_plugins(group='someapplication.plugins', location=__file__, attr='SomeClass')
        {'plugin1': <class module.plugins.plugin1.SomeClass at 0xdeadbeef>,
         'plugin2': <class module.plugins.plugin2.SomeClass at 0xcafebabe>,
         'plugname': <class myplugin.submodule.SomeClass at 0xbaadf00d>}

    """
    plugins = {}

    # If a path is specified, fetch all modules at the same level as the
    # given path.  This can also look into .egg files.
    if location:
        if os.path.splitext(location)[1] in ('.py', '.pyc', '.pyo'):
            # location is a file, so take the directory (probably __file__ was passed)
            location = os.path.dirname(location)
        if not location.endswith('/'):
            # Ensure location has a trialing /
            location += '/'

        if os.path.isdir(location):
            # location is an on-disk source tree.
            ls = os.listdir(location)
        elif '.egg/' in location:
            # location is an egg zip file.
            subpath = location.split('.egg/')[1]
            zip = zipimport.zipimporter(location)
            # Fetch list of all files inside the egg at the same level as the
            # given location.
            ls = [k[len(subpath):] for k in zip._files.keys() \
                                   if k.startswith(subpath) and k.count('/') == subpath.count('/')]

        # Insert the normalized location into the front of sys.path so that when we import
        # the plugins the location is searched first.
        sys.path.insert(0, location)
        try:
            for fname in ls:
                name, ext = os.path.splitext(fname)
                # don't attempt to import if file is not a python file or
                # directory.  Also, skip __init__.py from the location dir.
                if ext not in ('.py', 'pyc', '.pyo', '') or fname.startswith('__init__.py'):
                    continue

                allowed = filter(name) if filter else name
                # if filter returned a string, use that as module name.
                name = allowed if isinstance(allowed, basestring) else name
                if not allowed or name in plugins:
                    # filter returned zero value.
                    continue

                # Now we try to import the module
                try:
                    try:
                        # Import using the global scope of the caller, so
                        # that if the caller is module kaa.foo.bar, plugin
                        # baz is imported as kaa.foo.baz.
                        globs = scope or inspect.currentframe().f_back.f_globals
                    except (TypeError, KeyError):
                        globs = None
                    mod = __import__(name, globs)
                except Exception, e:
                    # Pass the exception back.
                    plugins[name] = e
                else:
                    # Import successful, add it to the plugins dict.
                    plugins[name] = getattr(mod, attr) if attr else mod
        finally:
            sys.path.pop(0)

    # If an entry point group was specified, fetch all entry points for that
    # group and load them into the plugins dict.
    if group:
        try:
            import pkg_resources
        except ImportError:
            # No setuptools.
            pass
        else:
            # Fetch a list of all entry points (defined as entry_points kwarg passed to
            # setup() for plugin modules) and load them, which returns the Plugin class
            # they were registered with.
            for entrypoint in pkg_resources.iter_entry_points(group):
                try:
                    plugins[entrypoint.name] = entrypoint.load()
                except Exception, e:
                    # Load failed, pass the exception back.
                    plugins[entrypoint.name] = e


    return plugins



# FIXME: this is not really what a Singleton is.  This should be called LazyObject
# or something.
class Singleton(object):
    """
    Create Singleton object from classref on demand.
    """

    class MemberFunction(object):
        def __init__(self, singleton, name):
            self._singleton = singleton
            self._name = name

        def __call__(self, *args, **kwargs):
            return getattr(self._singleton(), self._name)(*args, **kwargs)


    def __init__(self, classref):
        self._singleton = None
        self._class = classref

    def __call__(self):
        if self._singleton is None:
            self._singleton = self._class()
        return self._singleton

    def __getattr__(self, attr):
        if self._singleton is None:
            return Singleton.MemberFunction(self, attr)
        return getattr(self._singleton, attr)


# Python 2.6 and later has the enhanced property decorator (supports
# setters and deleters), but earlier versions don't, so for < 2.6
# we replace the built-in property to mimic the behaviour in 2.6+.
if sys.hexversion >= 0x02060000:
    # Bind built-in property to global name that we export.  So for 2.6+
    # kaa.utils.property is the built-in property.
    property = property
else:

    class property(property):
        """
        Replaces built-in property function to extend it as per
        http://bugs.python.org/issue1416
        """
        def __init__(self, fget = None, fset = None, fdel = None, doc = None):
            super(property, self).__init__(fget, fset, fdel)
            self.__doc__ = doc or fget.__doc__

        def _add_doc(self, prop, doc = None):
            prop.__doc__ = doc or self.__doc__
            return prop

        def setter(self, fset):
            if isinstance(fset, property):
                # Wrapping another property, use deleter.
                self, fset = fset, fset.fdel
            return self._add_doc(property(self.fget, fset, self.fdel))

        def deleter(self, fdel):
            if isinstance(fdel, property):
                # Wrapping another property, use setter.
                self, fdel = fdel, fdel.fset
            return self._add_doc(property(self.fget, self.fset, fdel))

        def getter(self, fget):
            return self._add_doc(property(fget, self.fset, self.fdel), fget.__doc__ or self.fget.__doc__)


def wraps(origfunc, lshift=0):
    """
    Decorator factory: used to create a decorator that assumes the same
    attributes (name, docstring, signature) as its decorated function when
    sphinx has been imported.  This is necessary because sphinx uses
    introspection to construct the documentation.

    This logic is inspired from Michele Simionato's decorator module.

        >>> def decorator(func):
        ...     @wraps(func)
        ...     def newfunc(*args, **kwargs):
        ...             # custom logic here ...
        ...             return func(*args, **kwargs)
        ...     return newfunc

    :param origfunc: the original function being decorated which is to be
                     wrapped.
    :param lshift: number of arguments to shift from the left of the original
                   function's call spec.  Wrapped function will have this
                   nubmer of arguments removed.
    :returns: a decorator which has the attributes of the decorated function.
    """
    if 'sphinx.builders' not in sys.modules:
        # sphinx not imported, so return a decorator that passes the func through.
        return functools.wraps(origfunc)
    elif lshift == 0:
        # Simple case, we don't need to munge args, so we can pass origfunc.
        return lambda func: origfunc

    # The idea here is to turn an origfunc with a signature like:
    #    origfunc(progress, a, b, c=42, *args, **kwargs)
    # into:
    #    lambda a, b, c=42, *args, **kwargs: log.error("...")
    spec = list(inspect.getargspec(origfunc))

    # Wrapped function needs a different signature.  Currently we can just
    # shift from the left of the args (e.g. for kaa.threaded progress arg).
    # FIXME: doesn't work if the shifted arg is a kwarg.
    spec[0] = spec[0][lshift:]

    if spec[-1]:
        # For the lambda signature's kwarg defaults, remap them into values
        # that can be referenced from the eval's local scope.  Otherwise only
        # intrinsics could be used as kwarg defaults.
        # Preserve old kwarg value list, to be passed into eval's locals scope.
        kwarg_values = spec[-1]
        # Changes (a=1, b=Foo) to a='__kaa_kw_defs[1]', b='__kaa_kw_defs[2]'
        sigspec = spec[:3] + [[ '__kaa_kw_defs[%d]' % n for n in range(len(spec[-1])) ]]
        sig = inspect.formatargspec(*sigspec)[1:-1]
        # Removes the quotes between __kaa_kw_defs[x]
        sig = re.sub(r"'(__kaa_kw_defs\[\d+\])'", '\\1', sig)
    else:
        sig = inspect.formatargspec(*spec)[1:-1]
        kwarg_values = None

    src = 'lambda %s: __kaa_log_.error("doc generation mode: decorated function \'%s\' was called")' % (sig, origfunc.__name__)
    def decorator(func):
        dec_func = eval(src, {'__kaa_log_': log, '__kaa_kw_defs': kwarg_values})
        return update_wrapper(dec_func, origfunc)
    return decorator


class DecoratorDataStore(object):
    """
    A utility class for decorators that sets or gets a value to/from a
    decorated function.  Attributes of instances of this class can be get, set,
    or deleted, and those attributes are associated with the decorated
    function.

    The object to which the data is attached is either the function itself for
    non-method, or the instance object for methods.

    There are two possible perspectives of using the data store: from inside
    the decorator, and from outside the decorator.  This allows, for example, a
    method to access data stored by one of its decorators.
    """
    def __init__(self, func, newfunc=None, newfunc_args=None, identifier=None):
        # Object the data will be stored in.
        target = func
        if hasattr(func, '__self__'):
            # Data store requested for a specific method.  Python 2.6+
            target = func.__self__
        elif hasattr(func, 'im_self'):
            # Data store requested for a specific method.  Python 2.5
            target = func.im_self

        # This kludge compares the code object of newfunc with the code object
        # of the first argument's attribute of the function's name.  If they're
        # the same, then we must be decorating a method, and we can use the
        # first argument (self) as the target.
        method = newfunc_args and getattr(newfunc_args[0], func.func_name, None)
        if method and newfunc.func_code == method.func_code:
            # Decorated function is a method, so store data in the instance.
            target = newfunc_args[0]

        self.__target = target
        # FIXME: user identifier only works when decorating methods.
        self.__name = identifier if identifier else func.func_name

    def __hash(self, key):
        return '__kaa_decorator_data_%s_%s' % (key, self.__name)

    def __getattr__(self, key):
        if key.startswith('_DecoratorDataStore__'):
            return super(DecoratorDataStore, self).__getattr__(key)
        return getattr(self.__target, self.__hash(key))

    def __setattr__(self, key, value):
        if key.startswith('_DecoratorDataStore__'):
            return super(DecoratorDataStore, self).__setattr__(key, value)
        return setattr(self.__target, self.__hash(key), value)

    def __hasattr__(self, key):
        return hasattr(self.__target, self.__hash(key))

    def __contains__(self, key):
        return hasattr(self.__target, self.__hash(key))

    def __delattr__(self, key):
        return delattr(self.__target, self.__hash(key))
