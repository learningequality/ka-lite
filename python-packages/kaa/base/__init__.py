# -*- coding: iso-8859-1 -*-
# -----------------------------------------------------------------------------
# __init__.py - main kaa init module
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
from __future__ import absolute_import
import sys
import os
import imp
import zipimport

# Import custom logger to update the Python logging module. Unfortunately. we
# can't import this lazy because we add logging.DEBUG2, and that should be
# available immediately after importing kaa.
from . import logger

# Exceptions can't be lazy proxied either, because there seems to be no magic
# method to detect when a class is being used in an except clause.  So all
# exceptions defined by core modules are put into a separate module which is
# imported explicitly.
from .errors import *

_object = object

# Enable on-demand importing of all modules.  Improves speed of importing kaa
# by almost 50x with warm cache (from 0.065s to 0.0015s) and 325x with cold
# cache (2.6s to 0.008s) on my system.  Although it does of course defer a lot
# of that time to later, it still improves overall performance because it only
# imports the files that actually get used during operation.
#
# Lazy importing should be completely user-transparent.  See the _LazyProxy
# docstring for more info.
#
# XXX: recognizing that this is a new feature and possibly (probably :))
# buggy, this constant lets you easily disable this functionality.
ENABLE_LAZY_IMPORTS = 1

def _activate():
    """
    Invoked when the first kaa object is accessed.  Lets us do initial
    bootstrapping, like replace the buggy system os.listdir.
    """
    if sys.hexversion < 0x02060000 and os.name == 'posix':
        # Python 2.5 (all point releases) have a bug with listdir on POSIX
        # systems causing improper out of memory exceptions.  We replace the
        # standard os.listdir with a version from kaa._utils that doesn't have
        # this bug, if _utils is available (it is optional).  Some distros will
        # have patched their 2.5 packages, but since we can't discriminate
        # those, we replace os.listdir regardless.
        #
        # See http://bugs.python.org/issue1608818
        try:
            from . import _utils
        except ImportError:
            pass
        else:
            os.listdir = _utils.listdir

    # Kill this function so it only gets invoked once.
    globals()['_activate'] = None


def _lazy_import(mod, names=None):
    """
    If lazy importing is enabled, creates _LazyProxy objects for each name
    specified in the names list and adds it to the global scope.  When
    the _LazyProxy object is accessed, 'mod' gets imported and the global
    name replaced with the actual object from 'mod'.

    If lazy importing is disabled, then names are imported from mod
    immediately, and then added to the global scope.  (It is equivalent
    to 'from mod import <names>')
    """
    if ENABLE_LAZY_IMPORTS:
        # Lazy importing is enabled, so created _LazyProxy classes.
        if names:
            # from mod import <names>
            for name in names:
                lazy = _LazyProxy(name, (_object,), {'_mod': mod, '_name': name, '_names': names})
                globals()[name] = lazy
        else:
            # import mod
            globals()[mod] = _LazyProxy(mod, (_object,), {'_mod': mod})
    else:
        # No lazy importing, import everything immediately.
        if globals()['_activate']:
            globals()['_activate']()
        omod = __import__(mod, globals(), fromlist=names)
        if names:
            # from mod import <names>
            for name in names:
                globals()[name] = getattr(omod, name)
        else:
            # import mod
            globals()[mod] = omod


class _LazyProxy(type):
    """
    Metaclass used to construct individual proxy classes for all names within
    the kaa namespace.  When the proxy class for a given name is accessed in
    any meaningful way the underlying module is imported and the name from
    that module replaces the _LazyProxy in the kaa namespace.

    By "meaninful" access, in each of the following code snippets, behaviour
    is as if the underlying module had been imported all along:

        # imports callable (repr() hook)
        >>> print kaa.Callable

        # imports process (dir() hook, but python 2.6 only; python 2.5 will
        # still automatically import, but dir() returns [])
        >>> dir(kaa.Process)

        # imports io (deep metaclass magic)
        >>> class MyIO(kaa.IOMonitor):
        ...    pass

        # imports io and callable (MI is supported)
        >>> class MyIO(kaa.IOMonitor, kaa.Callable):
        ...     pass

        # imports coroutine (== hook)
        >>> print policy == kaa.POLICY_PASS_LAST

        # imports main
        >>> kaa.main.run()

        # imports thread
        >>> @kaa.threaded()
        ... def foo():
        ...     pass

        # imports timer; this works, but it's suboptimal because it means the
        # user is _always_ interfacing through a proxy object.
        >>> from kaa import timed
        >>> @timed(1.0)
        ... def foo():
        ...     pass

        # imports core (setattr hook)
        >>> import kaa
        >>> kaa.Signal.MAX_CONNECTIONS = 10000

        # imports io (bitwise operator hook)
        >>> kaa.IO_READ | kaa.IO_WRITE
    """
    def __new__(cls, name, bases, dict):
        if bases == (_object,):
            # called by _lazy_import(), create a new LazyProxy class for the
            # given module/name, which is defined in dict.
            return type.__new__(cls, name, (_object,), dict)
        else:
            # called when something tries to subclass a LazyProxy.  Replace all
            # LazyProxy bases with the actual object (importing as needed) and
            # construct the new class subclassed from the newly imported kaa
            # objects.
            bases = ((b.__get() if type(b) == _LazyProxy else b) for b in bases)
            return type(name, tuple(bases), dict)


    def __get(cls):
        """
        Returns the underlying proxied object, importing the module if necessary.
        """
        try:
            return type.__getattribute__(cls, '_obj')[0]
        except AttributeError:
            pass

        if globals()['_activate']:
            # First kaa module loaded, invoke _activate()
            globals()['_activate']()

        mod = type.__getattribute__(cls, '_mod')
        try:
            names = type.__getattribute__(cls, '_names')
        except AttributeError:
            names = []

        # Keep a copy of the current global scope, see later for why.
        before = globals().copy()
        # Load the module and pull in the specified names.
        imp.acquire_lock()
        try:
            omod = __import__(mod, globals(), fromlist=names)
            if mod not in ('callable', 'utils', 'strutils', 'version'):
                # Any _other_ module needs the core modules.  main imports
                # core, nf_wrapper, timer, thread; thread imports async
                __import__('main', globals())

            if not names:
                # If we're here, we're proxying a whole module.
                # Replace LazyProxy in global scope with the actual newly loaded module.
                globals()[mod] = omod
                # kaa namespace has imported all these LazyProxy objects, so we must
                # replace them there too.
                setattr(sys.modules['kaa'], mod, omod)
                cls._obj = (omod,)
                return omod
            else:
                # Kludge: if we import a module with the same name as an existing
                # global (e.g.  coroutine, generator, signals), the module will
                # replace the _LazyProxy.  If a previous _LazyProxy has now been
                # replaced by a module, restore the original _LazyProxy.
                for key in before:
                    if type(before[key]) == _LazyProxy and type(globals().get(key)).__name__ == 'module':
                        globals()[key] = before[key]

                # Replace the _LazyProxy objects with the actual module attributes.
                for n in names:
                    attr = getattr(omod, n)
                    globals()[n] = attr
                    # Must also replace LazyProxy objects in kaa namespace.
                    setattr(sys.modules['kaa'], n, attr)

                name = type.__getattribute__(cls, '_name')
                obj = getattr(omod, name)
                # Store the object inside a tuple for future accesses (i.e. at the
                # top of this method).  Otherwise accessing cls._obj will invoke
                # _obj's get descriptor, if it exists, which we want to avoid.  For
                # example, if obj is a function, it will result in cls._obj being
                # an unbound method rather than the actual function.
                cls._obj = (obj,)
                return obj
        finally:
            imp.release_lock()


    def __getattribute__(cls, attr):
        # __get gets mangled
        if attr == '_LazyProxy__get':
            return type.__getattribute__(cls, attr)
        return getattr(cls.__get(), attr)

    def __setattr__(cls, attr, value):
        if attr == '_obj':
            return type.__setattr__(cls, attr, value)
        return setattr(cls.__get(), attr, value)

    def __getitem__(cls, item):
        return cls.__get()[item]

    def __setitem__(cls, item, value):
        cls.__get()[item] = value

    def __call__(cls, *args, **kwargs):
        return cls.__get()(*args, **kwargs)

    def __repr__(cls):
        return repr(cls.__get())

    def __str__(cls):
        return str(cls.__get())

    def __dir__(cls):
        # Python 2.6 only
        return dir(cls.__get())

    def __eq__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() == other

    def __or__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() | other

    def __and__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() & other

    def __cmp__(cls, other):
        # Python 2
        other = other.__get() if type(other) == _LazyProxy else other
        return cmp(cls.__get(), other)

    # Python 3+
    def __lt__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() < other

    def __le__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() <= other

    def __gt__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() > other

    def __ge__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get() >= other

    def __instancecheck__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get().__instancecheck__(other)

    def __subclasscheck__(cls, other):
        other = other.__get() if type(other) == _LazyProxy else other
        return cls.__get().__subclasscheck__(other)


# Version
_lazy_import('version', ['__version__'])

# Base object class for all kaa classes
_lazy_import('core', ['Object', 'Signal', 'Signals'])

# Callable classes
_lazy_import('callable', ['Callable', 'WeakCallable'])

# Notifier-aware callbacks do not need to be exported outside kaa.base
# _lazy_import('nf_wrapper', ['NotifierCallback', 'WeakNotifierCallback'])

# Async programming classes, namely InProgress
_lazy_import('async', [
    'InProgress', 'InProgressCallable', 'InProgressAny', 'InProgressAll',
    'InProgressStatus', 'inprogress',
    # Constants for InProgressAny/All finish argument.
    'FINISH_IDX', 'FINISH_RESULT', 'FINISH_SELF', 'FINISH_IDX_RESULT'
])

# Thread callables, helper functions and decorators
_lazy_import('thread', [
    'MainThreadCallable', 'ThreadPoolCallable', 'ThreadCallable', 'threaded',
    'synchronized', 'MAINTHREAD', 'ThreadInProgress', 'ThreadPool',
    'register_thread_pool', 'get_thread_pool'
])

# Timer classes and decorators
_lazy_import('timer', [
    'Timer', 'WeakTimer', 'OneShotTimer', 'WeakOneShotTimer', 'AtTimer',
    'OneShotAtTimer', 'timed', 'POLICY_ONCE', 'POLICY_MANY', 'POLICY_RESTART',
    'delay'
])

# IO/Socket handling
_lazy_import('io', ['IOMonitor', 'WeakIOMonitor', 'IO_READ', 'IO_WRITE', 'IOChannel'])
_lazy_import('sockets', ['Socket'])

# Event and event handler classes
_lazy_import('event', ['Event', 'EventHandler', 'WeakEventHandler'])

# coroutine decorator and helper classes
_lazy_import('coroutine', [
    'NotFinished', 'coroutine', 'CoroutineInProgress',
    # Constants for coroutine() policy argument
    'POLICY_SYNCHRONIZED', 'POLICY_SINGLETON', 'POLICY_PASS_LAST'
])

# generator support
_lazy_import('generator', ['Generator', 'generator'])

# process management
_lazy_import('process', ['Process'])

# special gobject thread support
_lazy_import('gobject', ['GOBJECT', 'gobject_set_threaded'])

# Import the two important strutils functions
_lazy_import('strutils', ['str_to_unicode', 'unicode_to_str', 'py3_str', 'py3_b'])

# Add tempfile support.
_lazy_import('utils', ['tempfile'])

# Expose main loop functions under kaa.main
_lazy_import('main')
_lazy_import('main', ['signals', 'wakeup', 'set_as_mainthread', 'is_mainthread'])

# kaa.base version
_lazy_import('version', ['VERSION'])

# We treat 'kaa' as both a namespace, where it houses all kaa sub-modules
# (e.g. import kaa.beacon), AND as a module, where it is essentially an alias
# for kaa base (e.g. kaa.Timer())
#
# Because of the latter, and because kaa.base is installed on the filesystem
# under kaa/base/, we need a custom import hook to translate imports for
# kaa.foo to kaa.base.foo when kaa.foo isn't a sub-module (like kaa.beacon).
#
# kaa.distribution.core automatically writes a kaa/__init__.py which does "from
# kaa.base import *" to pull everything from kaa.base into the kaa namespace.
# These import hooks are the second piece of the puzzle, to handle for example
# "import kaa.net.tls"
#
# XXX: it is not supported to have kaa.base installed as an egg but sub-modules
# installed as non-eggs.  Also, if kaa.base is installed as both an egg and a
# non-egg, the egg will always be loaded.  (Moral of the story, use only one or
# the other, do not mix eggs and non-eggs.)

class KaaLoader:
    """
    Custom loader used when kaa.foo is found as kaa.base.foo.
    """
    def __init__(self, info):
        self._info = info

    def load_module(self, name):
        fullname = 'kaa.base.' + name[4:]
        if fullname in sys.modules:
            return sys.modules[fullname]

        zipped = isinstance(self._info, zipimport.zipimporter)
        imp.acquire_lock()
        try:
            mod = imp.load_module(fullname, *self._info) if not zipped else self._info.load_module(fullname)
            # Cache loaded module as both kaa.foo (for external access) and
            # kaa.base.foo (for internal access by kaa.base code).
            sys.modules[name] = sys.modules[fullname] = mod
        finally:
            if not zipped and self._info[0]:
                self._info[0].close()
            imp.release_lock()

        return mod


class KaaFinder(_object):
    """
    Custom finder whose purposes is to intercept imports for kaa.foo, and,
    provided kaa.foo isn't a kaa sub-module (like kaa.beacon), attempt
    instead to import it as kaa.base.foo.

    Kaa modules __init__ stubs all do "from kaa.base import *" to pull the
    contents of kaa.base into the Kaa namespace.  This trick allows us to treat
    kaa both as a namespace for sub-modules and as a module (kaa.base).
    """
    def __init__(self):
        # zipimporter object to kaa.base when it is a zipped egg.
        self.zip = None
        self.last_sys_path = None


    def discover_kaa_eggs(self):
        if sys.path == self.last_sys_path:
            return
        self.kaa_eggs = {}
        for mod in sys.path:
            name = os.path.basename(mod)
            if name.startswith('kaa_') and mod.endswith('.egg'):
                # This is a kaa egg.  Convert kaa_foo-0.1.2.egg filename to
                # kaa.foo module name
                submod_name = 'kaa.' + name[4:].split('-')[0]
                self.kaa_eggs[submod_name] = mod
        self.last_sys_path = sys.path


    def find_module(self, name, path=None):
        # Ignore anything not in the form kaa.foo, or if kaa.foo is an egg in sys.path.
        self.discover_kaa_eggs()
        if not name.startswith('kaa.') or name.count('.') > 1 or name in self.kaa_eggs:
            return

        kaa_base_path = __file__.rsplit('/', 1)[0]
        name = name[4:].replace('.', '/')
        imp.acquire_lock()
        try:
            # Scenario 1: kaa.base is an on-disk tree (egg or otherwise)
            if not self.zip:
                try:
                    return KaaLoader(imp.find_module(name, [kaa_base_path]))
                except ImportError:
                    pass

            # Scenario 2: kaa.base is a zipped egg
            if '.egg/' in kaa_base_path and self.zip is not False:
                try:
                    if not self.zip:
                        self.zip = zipimport.zipimporter(kaa_base_path)
                except ImportError:
                    # Not a valid zipped egg, cache the result so we don't try again.
                    self.zip = False
                else:
                    if self.zip.find_module('kaa.base.' + name):
                        # kaa.base.foo found inside egg.
                        return KaaLoader(self.zip)
        finally:
            imp.release_lock()


# Now install our custom hooks.  Remove any existing KaaFinder import hooks, which
# could be caused by reload()ing.
[sys.meta_path.remove(x) for x in sys.meta_path if type(x).__name__ == 'KaaFinder']
sys.meta_path.append(KaaFinder())


# Allow access to old Callback names, but warn.  This will go away the release
# after next (probably 0.99.1).
def rename(oldcls, newcls):
    class Wrapper(_object):
        def __new__(cls, *args, **kwargs):
            import logging
            import traceback
            fname, line, c, content = traceback.extract_stack(limit=2)[0]
            log = logging.getLogger('kaa.base.core')
            log.warning('kaa.%s has been renamed to kaa.%s and will not be '
                        'available in kaa.base 1.0:\n%s (%s): %s',
                        oldcls, newcls.__name__, fname, line, content)
            # Replace old class with new class object, so we only warn once.
            globals()[oldcls] = newcls
            return newcls(*args, **kwargs)
    return Wrapper

Callback = rename('Callback', Callable)
WeakCallback = rename('WeakCallback', WeakCallable)
InProgressCallback = rename('InProgressCallback', InProgressCallable)
ThreadCallback = rename('ThreadCallback', ThreadCallable)
MainThreadCallback = rename('MainThreadCallback', MainThreadCallable)
NamedThreadCallback = rename('NamedThreadCallback', ThreadPoolCallable)
