# -----------------------------------------------------------------------------
# db.py - db abstraction module
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
    'Database', 'QExpr', 'DatabaseError', 'DatabaseReadOnlyError',
    'split_path', 'ATTR_SIMPLE', 'ATTR_SEARCHABLE', 'ATTR_IGNORE_CASE',
    'ATTR_INDEXED', 'ATTR_INDEXED_IGNORE_CASE', 'ATTR_INVERTED_INDEX',
    'RAW_TYPE'
]

# python imports
import sys
import os
import time
import re
import logging
import math
import cPickle
import copy_reg
import _weakref
import threading
try:
    # Try a system install of pysqlite
    from pysqlite2 import dbapi2 as sqlite
except ImportError:
    # Python 2.6 provides sqlite natively, so try that next.
    from sqlite3 import dbapi2 as sqlite

# kaa base imports
from .utils import property
from .strutils import py3_str, BYTES_TYPE, UNICODE_TYPE
from .timer import WeakOneShotTimer
from . import main

if sqlite.version < '2.1.0':
    raise ImportError('pysqlite 2.1.0 or higher required')
if sqlite.sqlite_version < '3.3.1':
    raise ImportError('sqlite 3.3.1 or higher required')

# get logging object
log = logging.getLogger('kaa.base.db')

SCHEMA_VERSION = 0.2
SCHEMA_VERSION_COMPATIBLE = 0.2
CREATE_SCHEMA = """
    CREATE TABLE meta (
        attr        TEXT UNIQUE,
        value       TEXT
    );
    INSERT INTO meta VALUES('version', %s);

    CREATE TABLE types (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        name            TEXT UNIQUE,
        attrs_pickle    BLOB,
        idx_pickle      BLOB
    );

    CREATE TABLE inverted_indexes (
        name            TEXT,
        attr            TEXT,
        value           TEXT
    );

    CREATE UNIQUE INDEX inverted_indexes_idx on inverted_indexes (name, attr);
"""

CREATE_IVTIDX_TEMPLATE = """
    CREATE TABLE ivtidx_%IDXNAME%_terms (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        term            TEXT,
        count           INTEGER
    );
    CREATE UNIQUE INDEX ivtidx_%IDXNAME%_terms_idx on ivtidx_%IDXNAME%_terms (term);

    CREATE TABLE ivtidx_%IDXNAME%_terms_map (
        rank            INTEGER,
        term_id         INTEGER,
        object_type     INTEGER,
        object_id       INTEGER,
        frequency       FLOAT
    );
    CREATE INDEX ivtidx_%IDXNAME%_terms_map_idx ON ivtidx_%IDXNAME%_terms_map (term_id, rank, object_type, object_id);
    CREATE INDEX ivtidx_%IDXNAME%_terms_map_object_idx ON ivtidx_%IDXNAME%_terms_map (object_id, object_type, term_id);
    CREATE TRIGGER ivtidx_%IDXNAME%_delete_terms_map DELETE ON ivtidx_%IDXNAME%_terms_map
    BEGIN
        UPDATE ivtidx_%IDXNAME%_terms SET count=MAX(0, count-1) WHERE id=old.term_id;
    END;
"""


ATTR_SIMPLE              = 0x01
ATTR_SEARCHABLE          = 0x02      # Is a SQL column, not a pickled field
ATTR_INDEXED             = 0x04      # Will have an SQL index
ATTR_IGNORE_CASE         = 0x08      # Store in db as lowercase for searches.
ATTR_INVERTED_INDEX      = 0x10      # Attribute associated with an inverted idx
ATTR_INDEXED_IGNORE_CASE = ATTR_INDEXED | ATTR_IGNORE_CASE

# These are special attributes for querying.  Attributes with
# these names cannot be registered.
RESERVED_ATTRIBUTES = ('id', 'parent', 'object', 'type', 'limit', 'attrs', 'distinct', 'orattrs')

STOP_WORDS = (
    "about", "and", "are", "but", "com", "for", "from", "how", "not",
    "some", "that", "the", "this", "was", "what", "when", "where", "who",
    "will", "with", "the", "www", "http", "org", "of", "on"
)


class PyObjectRow(object):
    """
    ObjectRows are dictionary-like objects that represent an object in
    the database.  They are used by pysqlite instead of tuples or indexes.

    ObjectRows support on-demand unpickling of the internally stored pickle
    which contains ATTR_SIMPLE attributes.

    This is the native Python implementation of ObjectRow.  There is a
    faster C implementation in the _objectrow extension.  This
    implementation is still designed to be efficient -- the C version is
    only about 60-70% faster.
    """
    # A dict containing per-query data: [refcount, idxmap, typemap, pickle_idx]
    # This is constructed once for each query, and each row returned in the
    # query references the same data.  Each ObjectRow instance adds to the
    # refcount once initialized, and is decremented when the object is deleted.
    # Once it reaches 0, the entry is removed from the dict.
    queries = {}
    # Use __slots__ as a minor optimization to improve object creation time.
    __slots__ = ('_description', '_object_types', '_type_name', '_row', '_pickle',
                '_idxmap', '_typemap', '_keys')
    def __init__(self, cursor, row, pickle_dict=None):
        # The following is done per row per query, so it should be as light as
        # possible.
        if pickle_dict:
            # Created outside pysqlite, e.g. from Database.add()
            self._pickle = pickle_dict
            self._idxmap = None
            return

        if isinstance(cursor, tuple):
            self._description, self._object_types = cursor
        else:
            self._description = cursor.description
            self._object_types = cursor._db()._object_types

        self._row = row
        # _pickle: False == no pickle present; None == pickle present but
        # empty; if a dict, is the unpickled dictionary; else it's a byte
        # string containing the pickled data.
        self._pickle = False
        self._type_name = row[0]
        try:
            attrs = self._object_types[self._type_name][1]
        except KeyError:
            raise ValueError("Object type '%s' not defined." % self._type_name)

        query_key = id(self._description)
        if query_key in PyObjectRow.queries:
            query_info = PyObjectRow.queries[query_key]
            # Increase refcount to the query info
            query_info[0] += 1
            self._idxmap, self._typemap, pickle_idx = query_info[1:]
            if pickle_idx != -1:
                self._pickle = self._row[pickle_idx]
            return

        # Everything below this is done once per query, not per row, so
        # performance isn't quite as critical.
        idxmap = {} # attr_name -> (idx, pickled, named_ivtdx, type, flags)
        pickle_idx = -1
        for i in range(2, len(self._description)):
            attr_name = self._description[i][0]
            idxmap[attr_name] = i
            if attr_name == 'pickle':
                pickle_idx = i
                self._pickle = self._row[i]

        for attr_name, (attr_type, flags, ivtidx, split) in attrs.items():
            idx = idxmap.get(attr_name, -1)
            pickled = flags & ATTR_SIMPLE or (flags & ATTR_INDEXED_IGNORE_CASE == ATTR_INDEXED_IGNORE_CASE)
            idxmap[attr_name] = idx, pickled, attr_name == ivtidx, attr_type, flags

        # Construct dict mapping type id -> type name.  Essentially an
        # inversion of _object_types
        typemap = dict((v[0], k) for k, v in self._object_types.items())

        self._idxmap = idxmap
        self._typemap = typemap
        PyObjectRow.queries[query_key] = [1, idxmap, typemap, pickle_idx]


    def __del__(self):
        if self._idxmap is None:
            # From Database.add(), pickle only, no pysqlite row.
            return
        query_key = id(self._description)
        query_info = PyObjectRow.queries[query_key]
        query_info[0] -= 1
        if query_info[0] == 0:
            # Refcount for this query info is 0, so remove from global queries
            # dict.
            del PyObjectRow.queries[query_key]


    def __getitem__(self, key):
        if self._idxmap is None:
            # From Database.add(), work strictly from pickle
            return self._pickle[key]
        elif key == 'type':
            return self._type_name
        elif key == 'parent':
            type_idx = self._idxmap.get('parent_type', [-1])[0]
            id_idx = self._idxmap.get('parent_id', [-1])[0]
            if type_idx == -1 or id_idx == -1:
                raise KeyError('Parent attribute not available')
            type_id = self._row[type_idx]
            return self._typemap.get(type_id, type_id), self._row[id_idx]
        elif key == '_row':
            return self._row
        elif isinstance(key, int):
            return self._row[key]

        attr = self._idxmap[key]
        attr_idx = attr[0]
        is_indexed_ignore_case = (attr[4] & ATTR_INDEXED_IGNORE_CASE == ATTR_INDEXED_IGNORE_CASE)
        if attr_idx == -1:
            # Attribute is not in the sql row
            if attr[1] and self._pickle is None:
                # Pickle is empty, which means this attribute was never
                # assigned a value.  Return a default (empty list if attribute
                # is named after an inverted index
                return [] if attr[2] else None
            elif not attr[1] or self._pickle is False:
                # The requested attribute is not in the sqlite row, and neither is the pickle.
                raise KeyError("ObjectRow does not have enough data to provide '%s'" % key)

        if not attr[1]:
            value = self._row[attr_idx]
        elif attr_idx >= 0 and not self._pickle and is_indexed_ignore_case:
            # Attribute is ATTR_INDEXED_IGNORE_CASE which means the
            # authoritative source is in the pickle, but we don't have it.  So just
            # return what we have.
            value = self._row[attr_idx]
        else:
            if self._pickle and not isinstance(self._pickle, dict):
                # We need to check the pickle but it's not unpickled, so do so now.
                self._pickle = dbunpickle(self._pickle)
            if is_indexed_ignore_case:
                key = '__' + key
            if key not in self._pickle:
                return [] if attr[2] else None
            else:
                value = self._pickle[key]

        if sys.hexversion < 0x03000000 and (attr[3] == str or attr[3] == buffer):
            # Python 2's pysqlite returns BLOBs as buffers.  If the attribute
            # type is string or buffer (RAW_TYPE on Python 2), convert to string.
            return str(value)
        else:
            return value


    def keys(self):
        if not self._idxmap:
            # Ad hoc ObjectRow, proxy to pickle dict.
            return self._pickle.keys()

        if not hasattr(self, '_keys'):
            self._keys = ['type']
            for name, attr in self._idxmap.items():
                if (attr[0] >= 0 or (attr[1] and self._pickle is not False)) and name != 'pickle':
                    self._keys.append(name)
            if 'parent_type' in self._idxmap and 'parent_id' in self._idxmap:
                self._keys.append('parent')
        return self._keys


    def values(self):
        if not self._idxmap:
            # Ad hoc ObjectRow, proxy to pickle dict.
            return self._pickle.values()
        return [self[k] for k in self.keys()]


    def items(self):
        return zip(self.keys(), self.values())


    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default


    def has_key(self, key):
        return key in self.keys()


    def __iter__(self):
        return iter(self.keys())


    def __contains__(self, key):
        if key == 'type' or (key == 'parent' and 'parent_id' in self._idxmap):
            return True
        else:
            return key in self._idxmap


if sys.hexversion >= 0x03000000:
    RAW_TYPE = bytes
    PICKLE_PROTOCOL = 3
    class Proto2Unpickler(pickle._Unpickler):
        """
        In spite of the promise that pickles will be compatible between Python
        releases, Python 3 does the wrong thing with non-unicode strings in
        pickles (BINSTRING pickle opcode).  It will try to convert them to
        unicode strings, which is wrong when the intention was to store binary
        data in a Python 2 str.

        This class implements a custom unpickler that will load BINSTRING as
        bytes objects.  An exception is made for dictionaries, where BINSTRING
        keys are converted to unicode strings.

        Additionally, it maps the unicode and buffer types to corresponding
        Python 3 types.
        """
        dispatch = pickle._Unpickler.dispatch.copy()
        def load_binstring(self):
            len = pickle.mloads(bytes('i', 'ascii') + self.read(4))
            self.append(bytes(self.read(len)))
        dispatch[pickle.BINSTRING[0]] = load_binstring

        def load_short_binstring(self):
            len = ord(self.read(1))
            self.append(bytes(self.read(len)))
        dispatch[pickle.SHORT_BINSTRING[0]] = load_short_binstring

        def load_setitems(self):
            super(Proto2Unpickler, self).load_setitems()
            d = self.stack[-1]
            for k, v in d.items():
                if type(k) == bytes:
                    sk = str(k, self.encoding, self.errors)
                    if sk not in d:
                        d[sk] = v
                        del d[k]
        dispatch[pickle.SETITEMS[0]] = load_setitems

        def find_class(self, module, name):
            if module == '__builtin__':
                if name == 'unicode':
                    return str
                elif name == 'buffer':
                    return bytes
            return super(Proto2Unpickler, self).find_class(module, name)

    def dbunpickle(s):
        if s[1] == 0x02:
            import io
            #import pickletools
            #pickletools.dis(io.BytesIO(bytes(s)))
            return Proto2Unpickler(io.BytesIO(bytes(s))).load()
        else:
            return pickle.loads(bytes(s))

    def dbpickle(value):
        return bytes(pickle.dumps(value, 3))

    # Need to be able to unpickle pickled buffers from Python 2.
    def _unpickle_buffer(s):
        return bytes(s)

else:
    RAW_TYPE = buffer
    PICKLE_PROTOCOL = 2
    def dbunpickle(s):
        return cPickle.loads(str(s))

    def dbpickle(value):
        return buffer(cPickle.dumps(value, 2))


    # Python2 can't pickle buffer types, so register a handler for that.
    def _pickle_buffer(b):
        return _unpickle_buffer, (str(b),)

    def _unpickle_buffer(s):
        return str(s)
    copy_reg.pickle(buffer, _pickle_buffer, _unpickle_buffer)


try:
    from . import _objectrow
except ImportError:
    # Use the python-native ObjectRow
    ObjectRow = PyObjectRow
else:
    # Use the faster C-based ObjectRow
    ObjectRow = _objectrow.ObjectRow
    # Expose the custom unpickler to the _objectrow module so it can deal with
    # pickles stored inside DB rows.
    _objectrow.dbunpickle = dbunpickle


# Register a handler for pickling ObjectRow objects.
def _pickle_ObjectRow(o):
    if o._description:
        return _unpickle_ObjectRow, ((o._description, o._object_types), o._row)
    else:
        return _unpickle_ObjectRow, (None, None, dict(o.items()))

def _unpickle_ObjectRow(*args):
    return ObjectRow(*args)

copy_reg.pickle(ObjectRow, _pickle_ObjectRow, _unpickle_ObjectRow)



PATH_SPLIT = re.compile(ur'(\d+)|[_\W]', re.U | re.X)
def split_path(s):
    """
    Convenience split function for inverted index attributes.  Useful for
    attributes that contain filenames.  Splits the given string s into
    components parts (directories, filename), discarding the extension and all
    but the last two directories.  What's remaining is split into words and the
    result is returned.
    """
    dirname, filename = os.path.split(s)
    fname_noext, ext = os.path.splitext(filename)
    for part in dirname.strip('/').split(os.path.sep)[2:][-2:] + [fname_noext]:
        for match in PATH_SPLIT.split(part):
            if match:
                yield match


# FIXME: this is flawed.  Can use placeholders by taking a n-tuple and
# replacing ? to (?, ?, ..., n) and then extend the query params list with the
# given tuple/list value.
def _list_to_printable(value):
    """
    Takes a list of mixed types and outputs a unicode string.  For
    example, a list [42, 'foo', None, "foo's' string"], this returns the
    string:

        (42, 'foo', NULL, 'foo''s'' string')

    Single quotes are escaped as ''.  This is suitable for use in SQL
    queries.
    """
    fixed_items = []
    for item in value:
        if isinstance(item, (int, long, float)):
           fixed_items.append(str(item))
        elif item == None:
            fixed_items.append("NULL")
        elif isinstance(item, UNICODE_TYPE):
            fixed_items.append("'%s'" % item.replace("'", "''"))
        elif isinstance(item, BYTES_TYPE):
            fixed_items.append("'%s'" % py3_str(item.replace("'", "''")))
        else:
            raise Exception, "Unsupported type '%s' given to _list_to_printable" % type(item)

    return '(' + ','.join(fixed_items) + ')'


class DatabaseError(Exception):
    pass

class DatabaseReadOnlyError(Exception):
    pass

class QExpr(object):
    """
    Flexible query expressions for use with :meth:`kaa.db.Database.query()`
    """
    def __init__(self, operator, operand):
        """
        :param operator: ``=``, ``!=``, ``<``, ``<=``, ``>``, ``>=``, ``in``,
                         ``not in``, ``range``, ``like``, or ``regexp``
        :type operator: str
        :param operand: the rvalue of the expression; any scalar values as part of
                        the operand must be the same type as the attribute being
                        evaluated

        Except for ``in``, ``not in``, and ``range``, the operand must be the
        type of the registered attribute being evaluated (e.g. unicode, int,
        etc.).

        The operand for ``in`` and ``not in`` are lists or tuples of the attribute
        type, to test inclusion in the given set.

        The ``range`` operator accepts a 2-tuple specifying min and max values
        for the attribute.  The Python expression age=QExpr('range', (20, 30))
        translates to ``age >= 20 AND age <= 30``.
        """
        operator = operator.lower()
        assert(operator in ('=', '!=', '<', '<=', '>', '>=', 'in', 'not in', 'range', 'like', 'regexp'))
        if operator in ('in', 'not in', 'range'):
            assert(isinstance(operand, (list, tuple)))
            if operator == 'range':
                assert(len(operand) == 2)

        self._operator = operator
        self._operand = operand

    def as_sql(self, var):
        if self._operator == "range":
            a, b = self._operand
            return "%s >= ? AND %s <= ?" % (var, var), (a, b)
        elif self._operator in ("in", "not in"):
            return "%s %s %s" % (var, self._operator.upper(),
                   _list_to_printable(self._operand)), ()
        else:
            return "%s %s ?" % (var, self._operator.upper()), \
                   (self._operand,)


class RegexpCache(object):
    def __init__(self):
        self.last_item = None
        self.last_expr = None

    def __call__(self, expr, item):
        if item is None:
            return 0

        if self.last_item == item and self.last_item is not None and self.last_expr == expr:
            return self.last_result
        if self.last_expr != expr:
            self.last_expr = re.compile(unicode(expr), re.U)

        self.last_item = item
        # FIXME: bad conversion to unicode!
        self.last_result = self.last_expr.match(unicode(item)) is not None
        return self.last_result


class Database(object):
    def __init__(self, dbfile):
        """
        Open a database, creating one if it doesn't already exist.

        :param dbfile: path to the database file
        :type dbfile: str

        SQLite is used to provide the underlying database.
        """
        super(Database, self).__init__()
        # _object_types dict is keyed on type name, where value is a 3-
        # tuple (id, attrs, idx), where:
        #   - id is a unique numeric database id for the type,
        #   - attrs is a dict containing registered attributes for the type,
        #     keyed on attribute name, where value is a 3-tuple of (type, flags,
        #     ivtidx), where type is a python datatype, flags is a bitmask of
        #     ATTR_*, ivtidx is the name of the associated inverted index (used
        #     if flags has ATTR_INVERTED_INDEX, otherwise None)
        #   - idx is a list of n-tuples, where each n-tuple defines two or more
        #     (non-ATTR_SIMPLE) attributes on which to create a multi-column
        #     sql index.
        self._object_types = {}

        # _inverted_indexes dict is keyed on index name, where value is
        # a dict keyed on:
        #   - min: minimum length of terms
        #   - max: maximum length of terms
        #   - ignore: list of terms to ignore
        #   - split: function or regular expression used to split string ATTR_INVERTED_INDEX
        #            attributes.
        self._inverted_indexes = {}

        # True when there are uncommitted changes
        self._dirty = False
        # True when modifications are not allowed to the database, which
        # is the case when Python 3 is opening a database created by Python 2
        # and upgrade_to_py3() has not been called.
        self._readonly = False
        self._dbfile = os.path.realpath(dbfile)
        self._lock = threading.RLock()
        self._lazy_commit_timer = WeakOneShotTimer(self.commit)
        self._lazy_commit_interval = None
        self._open_db()


    def _open_db(self):
        self._db = sqlite.connect(self._dbfile, check_same_thread=False)

        # Create the function "regexp" for the REGEXP operator of SQLite
        self._db.create_function("regexp", 2, RegexpCache())

        self._cursor = self._db.cursor()

        class Cursor(sqlite.Cursor):
            _db = _weakref.ref(self)
        self._db.row_factory = ObjectRow
        # Queries done through this cursor will use the ObjectRow row factory.
        self._qcursor = self._db.cursor(Cursor)

        for cursor in self._cursor, self._qcursor:
            cursor.execute("PRAGMA synchronous=OFF")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA cache_size=50000")
            cursor.execute("PRAGMA page_size=8192")

        if not self._check_table_exists("meta"):
            self._db.executescript(CREATE_SCHEMA % SCHEMA_VERSION)

        row = self._db_query_row("SELECT value FROM meta WHERE attr='version'")
        if float(row[0]) < SCHEMA_VERSION_COMPATIBLE:
            raise DatabaseError("Database '%s' has schema version %s; required %s" % \
                                (self._dbfile, row[0], SCHEMA_VERSION_COMPATIBLE))

        self._load_inverted_indexes()
        self._load_object_types()


    def _set_dirty(self):
        if self._lazy_commit_interval is not None:
            self._lazy_commit_timer.start(self._lazy_commit_interval)
        if self._dirty:
            return
        self._dirty = True
        main.signals['exit'].connect(self.commit)


    def _db_query(self, statement, args = (), cursor = None, many = False):
        t0=time.time()
        with self._lock:
            if not cursor:
                cursor = self._cursor
            if many:
                cursor.executemany(statement, args)
            else:
                cursor.execute(statement, args)
            rows = cursor.fetchall()
        t1=time.time()
        #print "QUERY [%.06f%s]: %s" % (t1-t0, ('', ' (many)')[many], statement), args
        return rows


    def _db_query_row(self, statement, args = (), cursor = None):
        rows = self._db_query(statement, args, cursor)
        if len(rows) == 0:
            return None
        return rows[0]


    def _to_obj_tuple(self, obj, numeric=False):
        """
        Returns a normalized object reference as a 2-tuple (type, id).

        :param obj: an ObjectRow, or 2-tuple (type, id)
        :param numeric: if True, coerce type name to a type id

        Raises ValueError if obj is not valid.
        """
        if isinstance(obj, ObjectRow):
            object_type, object_id = obj['type'], obj['id']
        else:
            try:
                object_type, object_id = obj
                if not isinstance(object_type, (int, basestring)) or not isinstance(object_id, (int, long, QExpr)):
                    raise TypeError
            except TypeError:
                raise ValueError('Object reference must be either ObjectRow, or (type, id), got %s' % obj)

        if numeric:
            object_type = self._get_type_id(object_type)

        return object_type, object_id


    def _check_table_exists(self, table):
        res = self._db_query_row("SELECT name FROM sqlite_master where " \
                                 "name=? and type='table'", (table,))
        return res != None


    def _register_check_indexes(self, indexes, attrs):
        for cols in indexes:
            if not isinstance(cols, (list, tuple)):
                raise ValueError, "Single column index specified ('%s') where multi-column index expected." % cols
            for col in cols:
                errstr = "Multi-column index (%s) contains" % ",".join(cols)
                if col not in attrs:
                    raise ValueError, "%s unknown attribute '%s'" % (errstr, col)
                if not attrs[col][1]:
                    raise ValueError, "%s ATTR_SIMPLE attribute '%s'" % (errstr, col)


    def _register_create_multi_indexes(self, indexes, table_name):
        for cols in indexes:
            self._db_query("CREATE INDEX %s_%s_idx ON %s (%s)" % \
                           (table_name, "_".join(cols), table_name, ",".join(cols)))


    def register_object_type_attrs(self, type_name, indexes = [], **attrs):
        """
        Register one or more object attributes and/or multi-column indexes for
        the given type name.

        This function modifies the database as needed to accommodate new
        indexes and attributes, either by creating the object's tables (in the
        case of a new object type) or by altering the object's tables to add
        new columns or indexes.

        This method is idempotent: if the attributes and indexes specified have
        not changed from previous invocations, no changes will be made to the
        database.  Moreover, newly registered attributes will not affect
        previously registered attributes.  This allows, for example, a plugin
        to extend an existing object type created by the core application
        without interfering with it.

        :param type_name: the name of object type the registered attributes or
                          indexes apply to.
        :type type_name: str
        :param indexes: a list of tuples where each tuple contains 2 or more
                        registered :attr:`~kaa.db.ATTR_SEARCHABLE` attributes
                        for which a composite index will be created in the
                        underlying database.  This is useful for speeding
                        up queries involving these attributes combined.
        :type indexes: list of tuples of strings
        :param attrs: keyword arguments defining the attributes to be
                      registered.  The keyword defining the attribute name
                      cannot conflict with any of the names in
                      :attr:`~kaa.db.RESERVED_ATTRIBUTES`.  See below for a
                      more complete specification of the value.
        :type attrs: 2, 3, or 4-tuple

        Previously registered attributes may be updated in limited ways (e.g.
        by adding an index to the attribute).  If the change requested is
        not supported, a ValueError will be raised.

        .. note:: Currently, indexes and attributes can only be added, not
           removed.  That is, once an attribute or index is added, it lives
           forever.

        Object attributes, which are supplied as keyword arguments, are either
        *searchable* or *simple*.  *Searchable* attributes occupy a column in
        the underlying database table and so queries can be performed on these
        attributes, but their types are more restricted.  *Simple* attributes
        can be any type that can be pickled, but can't be searched.

        The attribute kwarg value is a tuple of 2 to 4 items in length and in
        the form (attr_type, flags, ivtidx, split).

            * attr_type: the type of the object attribute. For simple attributes
              (:attr:`~kaa.db.ATTR_SIMPLE` in *flags*), this can be any picklable
              type; for searchable attributes (:attr:`~kaa.db.ATTR_SEARCHABLE`
              in *flags*), this must be either *int*, *float*, *str*, *unicode*,
              *bytes*, or *bool*.  (On Python 2.5, you can use ``kaa.db.RAW_TYPE``
              instead of *bytes*.)
            * flags: a bitmap of :ref:`attribute flags <attrflags>`
            * ivtidx: name of a previously registered inverted index used for
              this attribute. Only needed if flags contains
              :attr:`~kaa.db.ATTR_INVERTED_INDEX`
            * split: function or regular expression used to split string-based
              values for this attribute into separate terms for indexing.  If
              this isn't defined, then the default split strategy for the
              inverted index wil be used.

        Apart from not being allowed to conflict with one of the reserved
        names, there is a special case for attribute names: when they have
        the same name as a previously registered inverted index.  These
        attributes must be :attr:`~kaa.db.ATTR_SIMPLE`, and of type *list*.
        Terms explicitly associated with the attribute are persisted with the
        object, but when accessed, all terms for all attributes for that
        inverted index will be contained in the list, not just those explicitly
        associated with the same-named attribute.

        The following example shows what an application that indexes email might
        do::

            from kaa.db import *
            from datetime import datetime
            db = Database('email.db')
            db.register_inverted_index('keywords', min=3, max=30)
            db.register_object_type_attrs('msg',
                # Create a composite index on sender and recipient, because
                # (let's suppose) it's we do a lot of searches for specific
                # senders emailing specific recipients.
                [('sender', 'recipient')],

                # Simple attribute can be anything that's picklable, which datetime is.
                date = (datetime, ATTR_SIMPLE),

                # Sender and recipient names need to be ATTR_SEARCHABLE since
                # they're part of a composite index.
                sender = (unicode, ATTR_SEARCHABLE),
                recipient = (unicode, ATTR_SEARCHABLE),

                # Subject is searchable (standard SQL-based substring matches),
                # but also being indexed as part of the keywords inverted
                # index for fast term-based searching.
                subject = (unicode, ATTR_SEARCHABLE | ATTR_INVERTED_INDEX, 'keywords'),

                # Special case where an attribute name is the same as a registered
                # inverted index.  This lets us index on, for example, the message body
                # without actually storing the message inside the database.
                keywords = (list, ATTR_SIMPLE | ATTR_INVERTED_INDEX, 'keywords')
            )
        """
        if len(indexes) == len(attrs) == 0:
            raise ValueError, "Must specify indexes or attributes for object type"

        table_name = "objects_%s" % type_name

        # First pass over the attributes kwargs, sanity-checking provided values.
        for attr_name, attr_defn in attrs.items():
            # We allow attribute definition to be either a 2- to 4-tuple (last two
            # are optional), so pad the tuple with None if a 2- or 3-tuple was specified.
            attrs[attr_name] = attr_defn = tuple(attr_defn) + (None,) * (4-len(attr_defn))
            if len(attr_defn) != 4:
                raise ValueError, "Definition for attribute '%s' is not a 2- to 4-tuple." % attr_name

            # Verify the attribute flags contain either ATTR_SEARCHABLE or ATTR_SIMPLE;
            # it can't contain both as that doesn't make sense.
            if attr_defn[1] & (ATTR_SIMPLE | ATTR_SEARCHABLE) not in (ATTR_SIMPLE, ATTR_SEARCHABLE):
                raise ValueError, "Flags for attribute '%s' must contain exactly one " \
                                  "of ATTR_SIMPLE or ATTR_SEARCHABLE" % attr_name

            # Attribute name can't conflict with reserved names.
            if attr_name in RESERVED_ATTRIBUTES:
                raise ValueError, "Attribute name '%s' is reserved." % attr_name
            elif attr_name in self._inverted_indexes:
                if not attr_defn[1] & ATTR_INVERTED_INDEX or attr_defn[2] != attr_name:
                    # Attributes can be named after inverted indexes, but only if
                    # ATTR_INVERTED_INDEX is specified and the attribute name is the
                    # same as its ivtidx name.
                    raise ValueError, "Attribute '%s' conflicts with inverted index of same name, " \
                                      "but ATTR_INVERTED_INDEX not specified in flags." % attr_name

            if attr_defn[1] & ATTR_INVERTED_INDEX:
                # Attributes with ATTR_INVERTED_INDEX can only be certain types.
                if attr_defn[0] not in (str, unicode, tuple, list, set):
                    raise TypeError, "Type for attribute '%s' must be string, unicode, list, tuple, or set " \
                                     "because it is ATTR_INVERTED_INDEX" % attr_name

                # Make sure inverted index name is valid.
                if attr_defn[2] is None:
                    raise ValueError, "Attribute '%s' flags specify inverted index, " \
                                      "but no inverted index name supplied." % attr_name
                elif attr_defn[2] not in self._inverted_indexes:
                    raise ValueError, "Attribute '%s' specifies undefined interverted index '%s'" % \
                                      (attr_name, attr_defn[2])

            # Compile split regexp if it was given.
            if attr_defn[3] is not None and not callable(attr_defn[3]):
                attrs[attr_name] = attr_defn[:3] + (re.compile(attr_defn[3]),)


        if type_name in self._object_types:
            # This type already exists.  Compare given attributes with
            # existing attributes for this type to see what needs to be done
            # (if anything).
            cur_type_id, cur_type_attrs, cur_type_idx = self._object_types[type_name]
            new_attrs = {}
            table_needs_rebuild = False
            changed = False
            for attr_name, attr_defn in attrs.items():
                attr_type, attr_flags, attr_ivtidx, attr_split = attr_defn
                # TODO: converting an attribute from SIMPLE to SEARCHABLE or vice
                # versa isn't supported yet.  Raise exception here to prevent
                # potential data loss.
                if attr_name in cur_type_attrs and attr_flags & (ATTR_SEARCHABLE | ATTR_SIMPLE) != \
                   cur_type_attrs[attr_name][1] & (ATTR_SEARCHABLE | ATTR_SIMPLE):
                   raise ValueError, "Unsupported attempt to convert attribute '%s' " \
                                     "between ATTR_SIMPLE and ATTR_SEARCHABLE" % attr_name

                if attr_name not in cur_type_attrs or cur_type_attrs[attr_name] != attr_defn:
                    # There is a new attribute specified for this type, or an
                    # existing one has changed.
                    new_attrs[attr_name] = attr_defn
                    changed = True
                    if attr_flags & ATTR_SEARCHABLE:
                        # New attribute isn't simple, needs to alter table.
                        table_needs_rebuild = True
                    elif attr_flags & ATTR_INVERTED_INDEX:
                        # TODO: there is no need to rebuild the table when adding/modifying
                        # an ATTR_SIMPLE | ATTR_INVERTED_INDEX attribute, we just need to
                        # recreate the delete trigger (and remove any rows from the
                        # inverted index's map for this object type if we're removing
                        # an association with that ivtidx).  For now we will force a
                        # rebuild since I'm too lazy to implement the proper way.
                        table_needs_rebuild = True

                        if attr_name in cur_type_attrs and not cur_type_attrs[attr_name][1] & ATTR_INVERTED_INDEX:
                            # FIXME: if we add an inverted index to an existing attribute, we'd
                            # need to reparse that attribute in all rows to populate the inverted
                            # map.  Right now just log a warning.
                            log.warning("Adding inverted index '%s' to existing attribute '%s' not fully " \
                                        "implemented; index may be out of sync.", attr_ivtidx, attr_name)

            if not changed:
                return
            if self._readonly:
                raise DatabaseReadOnlyError('upgrade_to_py3() must be called before database can be modified')

            # Update the attr list to merge both existing and new attributes.
            attrs = cur_type_attrs.copy()
            attrs.update(new_attrs)
            new_indexes = set(indexes).difference(cur_type_idx)
            indexes = set(indexes).union(cur_type_idx)
            self._register_check_indexes(indexes, attrs)

            if not table_needs_rebuild:
                # Only simple (i.e. pickled only) attributes are being added,
                # or only new indexes are added, so we don't need to rebuild the
                # table.
                if len(new_attrs):
                    self._db_query("UPDATE types SET attrs_pickle=? WHERE id=?", (dbpickle(attrs), cur_type_id))

                if len(new_indexes):
                    self._register_create_multi_indexes(new_indexes, table_name)
                    self._db_query("UPDATE types SET idx_pickle=? WHERE id=?", (dbpickle(indexes), cur_type_id))

                self.commit()
                self._load_object_types()
                return

            # We need to update the database now ...

        else:
            # New type definition.  Populate attrs with required internal
            # attributes so they get created with the table.

            new_attrs = cur_type_id = None
            # Merge standard attributes with user attributes for this new type.
            attrs.update({
                'id': (int, ATTR_SEARCHABLE, None, None),
                'parent_type': (int, ATTR_SEARCHABLE, None, None),
                'parent_id': (int, ATTR_SEARCHABLE, None, None),
                'pickle': (RAW_TYPE, ATTR_SEARCHABLE, None, None)
            })
            self._register_check_indexes(indexes, attrs)

        create_stmt = 'CREATE TABLE %s_tmp (' % table_name

        # Iterate through type attributes and append to SQL create statement.
        sql_types = {int: 'INTEGER', long: 'INTEGER', float: 'FLOAT', RAW_TYPE: 'BLOB',
                     UNICODE_TYPE: 'TEXT', BYTES_TYPE: 'BLOB', bool: 'INTEGER', basestring: 'TEXT'}
        for attr_name, (attr_type, attr_flags, attr_ivtidx, attr_split) in attrs.items():
            if attr_flags & ATTR_SEARCHABLE:
                # Attribute needs to be a column in the table, not a pickled value.
                if attr_type not in sql_types:
                    raise ValueError, "Type '%s' not supported" % str(attr_type)
                create_stmt += '%s %s' % (attr_name, sql_types[attr_type])
                if attr_name == 'id':
                    # Special case, these are auto-incrementing primary keys
                    create_stmt += ' PRIMARY KEY AUTOINCREMENT'
                create_stmt += ','

        create_stmt = create_stmt.rstrip(',') + ')'
        self._db_query(create_stmt)


        # Add this type to the types table, including the attributes
        # dictionary.
        self._db_query('INSERT OR REPLACE INTO types VALUES(?, ?, ?, ?)',
                       (cur_type_id, type_name, dbpickle(attrs), dbpickle(indexes)))

        # Sync self._object_types with the object type definition we just
        # stored to the db.
        self._load_object_types()

        if new_attrs:
            # Migrate rows from old table to new temporary one.  Here we copy only
            # ATTR_SEARCHABLE columns that exist in both old and new definitions.
            columns = filter(lambda x: cur_type_attrs[x][1] & ATTR_SEARCHABLE and \
                                       x in attrs and attrs[x][1] & ATTR_SEARCHABLE, cur_type_attrs.keys())
            columns = ','.join(columns)
            self._db_query('INSERT INTO %s_tmp (%s) SELECT %s FROM %s' % \
                           (table_name, columns, columns, table_name))

            # Delete old table.
            self._db_query('DROP TABLE %s' % table_name)

        # Rename temporary table.
        self._db_query('ALTER TABLE %s_tmp RENAME TO %s' % (table_name, table_name))

        # Increase the objectcount for new inverted indexes, and create a
        # trigger that reduces the objectcount for each applicable inverted
        # index when a row is deleted.
        inverted_indexes = self._get_type_inverted_indexes(type_name)
        if inverted_indexes:
            n_rows = self._db_query_row('SELECT COUNT(*) FROM %s' % table_name)[0]
            sql = 'CREATE TRIGGER delete_object_%s DELETE ON %s BEGIN ' % (type_name, table_name)
            for idx_name in inverted_indexes:
                sql += "UPDATE inverted_indexes SET value=MAX(0, value-1) WHERE name='%s' AND attr='objectcount';" % idx_name
                # Add to objectcount (both in db and cached value)
                self._db_query("UPDATE inverted_indexes SET value=value+? WHERE name=? and attr='objectcount'",
                               (n_rows, idx_name))
                self._inverted_indexes[idx_name]['objectcount'] += n_rows
            sql += 'END'
            self._db_query(sql)

        # Create index for locating all objects under a given parent.
        self._db_query("CREATE INDEX %s_parent_idx on %s (parent_id, "\
                       "parent_type)" % (table_name, table_name))

        # If any of these attributes need to be indexed, create the index
        # for that column.
        for attr_name, (attr_type, attr_flags, attr_ivtidx, attr_split) in attrs.items():
            if attr_flags & ATTR_INDEXED:
                self._db_query("CREATE INDEX %s_%s_idx ON %s (%s)" % \
                               (table_name, attr_name, table_name, attr_name))

        # Create multi-column indexes; indexes value has already been verified.
        self._register_create_multi_indexes(indexes, table_name)
        self.commit()


    def register_inverted_index(self, name, min = None, max = None, split = None, ignore = None):
        """
        Registers a new inverted index with the database.

        An inverted index maps arbitrary terms to objects and allows you to
        query based on one or more terms.  If the inverted index already exists
        with the given parameters, no action is performed.

        :param name: the name of the inverted index; must be alphanumeric.
        :type name: str
        :param min: the minimum length of terms to index; terms smaller
                    than this will be ignored.  If None (default), there
                    is no minimum size.
        :type min: int
        :param max: the maximum length of terms to index; terms larger than
                    this will be ignored.  If None (default), there is no
                    maximum size.
        :type max: int
        :param split: used to parse string-based attributes using this inverted
                      index into individual terms.  In the case of regexps, the
                      split method will be called.  (If a string is specified,
                      it will be compiled into a regexp first.)  If *split* is
                      a callable, it will receive a string of text and must return
                      a sequence, and each item in the sequence will be indexed
                      as an individual term.  If split is not specified, the
                      default is to split words at non-alphanumeric/underscore/digit
                      boundaries.
        :type split: callable, regexp (SRE_Pattern) object, or str
        :param ignore: a list of terms that will not be indexed (so-called
                       *stop words*).  If specified, each indexed term for this
                       inverted index will first be checked against this list.
                       If it exists, the term is discarded.

        For example::

            from kaa.db import *
            db = Database('test.db')
            db.register_inverted_index('tags')
            db.register_inverted_index('keywords', min=3, max=30, ignore=STOP_WORDS)
        """
        # Verify specified name doesn't already exist as some object attribute.
        for object_name, object_type in self._object_types.items():
            if name in object_type[1] and name != object_type[1][name][2]:
                raise ValueError, "Inverted index name '%s' conflicts with registered attribute in object '%s'" % \
                                  (name, object_name)

        if split is None:
            # Default split regexp is to split words on
            # alphanumeric/digits/underscore boundaries.
            split = re.compile(u"(\d+)|[_\W]", re.U)
        elif isinstance(split, basestring):
            split = re.compile(py3_str(split), re.U)

        if name not in self._inverted_indexes and not self._readonly:
            self._db_query('INSERT INTO inverted_indexes VALUES(?, "objectcount", 0)', (name,))
            # Create the tables needed by the inverted index.
            with self._lock:
                self._db.executescript(CREATE_IVTIDX_TEMPLATE.replace('%IDXNAME%', name))
        elif name in self._inverted_indexes:
            defn = self._inverted_indexes[name]
            if min == defn['min'] and max == defn['max'] and split == defn['split'] and \
               ignore == defn['ignore']:
               # Definition unchanged, nothing to do.
               return

        if self._readonly:
            raise DatabaseReadOnlyError('upgrade_to_py3() must be called before database can be modified')

        defn = {
            'min': min,
            'max': max,
            'split': split,
            'ignore': ignore,
        }

        self._db_query("INSERT OR REPLACE INTO inverted_indexes VALUES(?, 'definition', ?)",
                       (name, dbpickle(defn)))

        defn['objectcount'] = 0
        self._inverted_indexes[name] = defn
        self.commit()


    def _load_inverted_indexes(self):
        for name, attr, value in self._db_query("SELECT * from inverted_indexes"):
            if name not in self._inverted_indexes:
                self._inverted_indexes[name] = {}
            if attr == 'objectcount':
                self._inverted_indexes[name][attr] = int(value)
            elif attr == 'definition':
                self._inverted_indexes[name].update(dbunpickle(value))


    def _load_object_types(self):
        is_pickle_proto_2 = False
        for id, name, attrs, idx in self._db_query("SELECT * from types"):
            if attrs[1] == 0x02 or idx[1] == 0x02:
                is_pickle_proto_2 = True
            self._object_types[name] = id, dbunpickle(attrs), dbunpickle(idx)

        if sys.hexversion >= 0x03000000 and is_pickle_proto_2:
            self._readonly = True
            log.warning('kaa.db databases created by Python 2 are read-only until upgrade_to_py3() is called')


    def _get_type_inverted_indexes(self, type_name):
        if type_name not in self._object_types:
            return []

        indexed_attrs = set()
        type_attrs = self._object_types[type_name][1]
        for name, (attr_type, flags, attr_ivtidx, attr_split) in type_attrs.items():
            if flags & ATTR_INVERTED_INDEX:
                indexed_attrs.add(attr_ivtidx)

        return list(indexed_attrs)


    def _get_type_attrs(self, type_name):
        return self._object_types[type_name][1]

    def _get_type_id(self, type_name):
        return self._object_types[type_name][0]


    def _make_query_from_attrs(self, query_type, attrs, type_name):
        type_attrs = self._get_type_attrs(type_name)

        # True if an attribute from the pickle was removed and we must force an update.
        pickle_attr_removed = False
        columns = []
        values = []
        placeholders = []

        for key in attrs.keys():
            if key not in type_attrs:
                if key in self._inverted_indexes:
                    continue
                raise ValueError("Reference to undefined attribute '%s' for type '%s'" % (key, type_name))
            if attrs[key] == None:
                # Remove all None attributes (even ATTR_SEARCHABLE), otherwise we will
                # raise a TypeError later, since NoneType isn't the right type.
                if type_attrs[key][1] & ATTR_SIMPLE:
                    # Attribute removed from a pickle, be sure we update the pickle in
                    # the db if this is an 'update' query_type.
                    pickle_attr_removed = True
                del attrs[key]

        attrs_copy = attrs.copy()
        for name, (attr_type, flags, attr_ivtidx, attr_split) in type_attrs.items():
            if flags & ATTR_SEARCHABLE and name in attrs:
                columns.append(name)
                placeholders.append("?")
                value = attrs[name]
                # Coercion for numeric types
                if isinstance(value, (int, long, float)) and attr_type in (int, long, float):
                    value = attr_type(value)
                elif isinstance(value, basestring) and \
                     flags & ATTR_INDEXED_IGNORE_CASE == ATTR_INDEXED_IGNORE_CASE:
                    # If the attribute is ATTR_INDEXED_IGNORE_CASE and it's a string
                    # then we store it as lowercase in the table column, while
                    # keeping the original (unchanged case) value in the pickle.
                    # This allows us to do case-insensitive searches on indexed
                    # columns and still benefit from the index.
                    attrs_copy["__" + name] = value
                    value = value.lower()

                if not isinstance(value, attr_type):
                    raise TypeError("Type mismatch in query for %s: '%s' (%s) is not a %s" % \
                                    (name, str(value), str(type(value)), str(attr_type)))
                if attr_type == BYTES_TYPE:
                    # For Python 2, convert non-unicode strings to buffers.  (For Python 3,
                    # BYTES_TYPE == RAW_TYPE so this is a no-op.)
                    value = RAW_TYPE(value)
                values.append(value)
                del attrs_copy[name]

        if len(attrs_copy) > 0 or (pickle_attr_removed and query_type == 'update'):
            # From the remaining attributes, remove those named after inverted
            # indexes that aren't explicitly registered as attributes in the
            # object type.  Here is where we keep our cached copy of inverted
            # index terms.
            for attr in attrs_copy.keys():
                if attr in self._inverted_indexes and attr not in type_attrs:
                    del attrs_copy[attr]

            # What's left gets put into the pickle.
            columns.append("pickle")
            values.append(dbpickle(attrs_copy))
            placeholders.append("?")

        table_name = "objects_" + type_name

        if query_type == "add":
            if columns:
                columns = ",".join(columns)
                placeholders = ",".join(placeholders)
                q = "INSERT INTO %s (%s) VALUES(%s)" % (table_name, columns, placeholders)
            else:
                # Insert empty row (need to specify at least one column to make valid
                # SQL, so just specify id of null, which will assume next value in
                # sequence.
                q = 'INSERT INTO %s (id) VALUES(null)' % table_name
        else:
            q = "UPDATE %s SET " % table_name
            for col, ph in zip(columns, placeholders):
                q += "%s=%s," % (col, ph)
            # Trim off last comma
            q = q.rstrip(",")
            q += " WHERE id=?"
            values.append(attrs["id"])

        return q, values


    def delete(self, obj):
        """
        Delete the specified object.

        :param obj: the object to delete
        :type obj: :class:`ObjectRow` or (object_type, object_id)
        """
        # TODO: support recursive delete (delete all decendents)
        object_type, object_id = self._to_obj_tuple(obj)
        return self._delete_multiple_objects({object_type: (object_id,)})


    def reparent(self, obj, parent):
        """
        Change the parent of an object.

        :param obj: the object to reparent
        :type obj: :class:`ObjectRow`, or (type, id)
        :param parent: the new parent of the object
        :type parent: :class:`ObjectRow`, or (type, id)

        This is a convenience method to improve code readability, and is
        equivalent to::

            database.update(obj, parent=parent)
        """
        return self.update(obj, parent=parent)


    def retype(self, obj, new_type):
        """
        Convert the object to a new type.

        :param obj: the object to be converted to the new type
        :type obj: :class:`ObjectRow`, or (type, id)
        :param new_type: the type to convert the object to
        :type newtype: str
        :returns: an :class:`ObjectRow`, converted to the new type with the new id

        Any attribute that has not also been registered with ``new_type``
        (and with the same name) will be removed.  Because the object is
        effectively changing ids, all of its existing children will be
        reparented to the new id.
        """

        if new_type not in self._object_types:
            raise ValueError('Parent type %s not registered in database' % new_type)

        # Reload and force pickled attributes into the dict.
        try:
            attrs = dict(self.get(obj))
        except TypeError:
            raise ValueError('Object (%s, %s) is not found in database' % (obj['type'], obj['id']))

        parent = attrs.get('parent')
        # Remove all attributes that aren't also in the destination type.  Also
        # remove type, id, and parent attrs, which get regenerated when we add().
        for attr_name in attrs.keys():
            # TODO: check src and dst attr types and try to coerce, and if
            # not possible, raise an exception.
            if attr_name not in self._object_types[new_type][1] or attr_name in ('type', 'id', 'parent'):
                del attrs[attr_name]

        new_obj = self.add(new_type, parent, **attrs)
        # Reparent all current children to the new id.
        for child in self.query(parent=obj):
            # TODO: if this raises, delete new_obj (to rollback) and reraise.
            self.reparent(child, new_obj)

        self.delete(obj)
        return new_obj


    def delete_by_query(self, **attrs):
        """
        Delete all objects returned by the given query.

        :param attrs: see :meth:`~kaa.db.Database.query` for details.
        :returns: the number of objects deleted
        :rtype: int
        """
        attrs["attrs"] = ["id"]
        results = self.query(**attrs)
        if len(results) == 0:
            return 0

        results_by_type = {}
        for o in results:
            if o["type"] not in results_by_type:
                results_by_type[o["type"]] = []
            results_by_type[o["type"]].append(o["id"])

        return self._delete_multiple_objects(results_by_type)


    def _delete_multiple_objects(self, objects):
        if self._readonly:
            raise DatabaseReadOnlyError('upgrade_to_py3() must be called before database can be modified')

        child_objects = {}
        count = 0
        for object_type, object_ids in objects.items():
            ivtidxes = self._get_type_inverted_indexes(object_type)
            self._delete_multiple_objects_inverted_index_terms({object_type: (ivtidxes, object_ids)})
            object_type_id = self._get_type_id(object_type)
            if len(object_ids) == 0:
                continue

            object_ids_str = _list_to_printable(object_ids)
            self._db_query("DELETE FROM objects_%s WHERE id IN %s" % \
                           (object_type, object_ids_str))
            count += self._cursor.rowcount

            # Record all children of this object so we can later delete them.
            for tp_name, (tp_id, tp_attrs, tp_idx) in self._object_types.items():
                children_ids = self._db_query("SELECT id FROM objects_%s WHERE parent_id IN %s AND parent_type=?" % \
                                              (tp_name, object_ids_str), (object_type_id,))
                if len(children_ids):
                    child_objects[tp_name] = [x[0] for x in children_ids]

        if len(child_objects):
            # If there are any child objects of the objects we just deleted,
            # delete those now.
            count += self._delete_multiple_objects(child_objects)

        if count:
            self._set_dirty()
        return count


    def add(self, object_type, parent=None, **attrs):
        """
        Add an object to the database.

        :param object_type: the name of the object type previously created by
                            :meth:`~kaa.db.Database.register_object_type_attrs`.
        :type object_type: str
        :param parent: specifies the parent of this object, if any; does not have
                       to be an object of the same type.
        :type parent: :class:`ObjectRow` or 2-tuple (object_type, object_id)
        :param attrs: keyword arguments specifying the attribute (which must
                      have been registered) values.  Registered attributes that
                      are not explicitly specified here will default to None.
        :returns: :class:`ObjectRow` representing the added object

        For example::

            import os
            from kaa.db import *
            db = Database('test.db')
            db.register_object_type_attrs('directory',
                name = (str, ATTR_SEARCHABLE),
                mtime = (float, ATTR_SIMPLE)
            )
            root = db.add('directory', name='/', mtime=os.stat('/').st_mtime)
            db.add('directory', parent=root, name='etc', mtime=os.stat('/etc').st_mtime)
            db.add('directory', parent=root, name='var', mtime=os.stat('/var').st_mtime)
        """
        if self._readonly:
            raise DatabaseReadOnlyError('upgrade_to_py3() must be called before database can be modified')

        type_attrs = self._get_type_attrs(object_type)
        if parent:
            attrs['parent_type'], attrs['parent_id'] = self._to_obj_tuple(parent, numeric=True)

        # Increment objectcount for the applicable inverted indexes.
        inverted_indexes = self._get_type_inverted_indexes(object_type)
        if inverted_indexes:
            self._db_query("UPDATE inverted_indexes SET value=value+1 WHERE attr='objectcount' AND name IN %s" % \
                           _list_to_printable(inverted_indexes))


        # Process inverted index maps for this row
        ivtidx_terms = []
        for ivtidx in inverted_indexes:
            # Sync cached objectcount with the DB (that we just updated above)
            self._inverted_indexes[ivtidx]['objectcount'] += 1
            terms_list = []
            split = self._inverted_indexes[ivtidx]['split']
            for name, (attr_type, flags, attr_ivtidx, attr_split) in type_attrs.items():
                if attr_ivtidx == ivtidx and name in attrs:
                    terms_list.append((attrs[name], 1.0, attr_split or split, ivtidx))

            if ivtidx in attrs and ivtidx not in type_attrs:
                # Attribute named after an inverted index is given in kwagrs,
                # but that ivtidx is not a registered attribute (which would be
                # handled in the for loop just above).
                terms_list.append((attrs[ivtidx], 1.0, split, ivtidx))

            terms = self._score_terms(terms_list)
            if terms:
                ivtidx_terms.append((ivtidx, terms))
                # If there are no terms for this ivtidx, we don't bother storing
                # an empty list in the pickle.
                if ivtidx in type_attrs:
                    # Registered attribute named after ivtidx; store ivtidx
                    # terms in object.
                    attrs[ivtidx] = terms.keys()

        query, values = self._make_query_from_attrs("add", attrs, object_type)
        self._db_query(query, values)

        # Add id given by db, as well as object type.
        attrs['id'] = self._cursor.lastrowid
        attrs['type'] = unicode(object_type)
        attrs['parent'] = self._to_obj_tuple(parent) if parent else (None, None)

        for ivtidx, terms in ivtidx_terms:
            self._add_object_inverted_index_terms((object_type, attrs['id']), ivtidx, terms)

        # Populate dictionary with keys for this object type not specified in kwargs.
        attrs.update(dict.fromkeys([k for k in type_attrs if k not in attrs.keys() + ['pickle']]))

        self._set_dirty()
        return ObjectRow(None, None, attrs)


    def get(self, obj):
        """
        Fetch the given object from the database.

        :param obj: a 2-tuple (type, id) representing the object.
        :returns: :class:`ObjectRow`

        obj may also be an :class:`ObjectRow`, however that usage is less
        likely to be useful, because an :class:`ObjectRow` already contains all
        information about the object.  One common use-case is to reload a
        possibly changed object from disk.

        This method is essentially shorthand for::

           database.query(object=(object_type, object_id))[0]
        """
        obj = self._to_obj_tuple(obj)
        rows = self.query(object=obj)
        if rows:
            return rows[0]


    def update(self, obj, parent=None, **attrs):
        """
        Update attributes for an existing object in the database.

        :param obj: the object whose attributes are being modified
        :type obj: :class:`ObjectRow` or 2-tuple (object_type, object_id)
        :param parent: if specified, the object is reparented to the given
                       parent object, otherwise the parent remains the
                       same as when the object was added with
                       :meth:`~kaa.db.Database.add`.
        :type parent: :class:`ObjectRow` or 2-tuple (object_type, object_id)
        :param attrs: keyword arguments specifying the attribute (which must
                      have been registered) values.  Registered attributes that
                      are not explicitly specified here will preserve their
                      original values (except for special attributes named
                      after inverted index; see warning below).

        Continuing from the example in :meth:`~kaa.db.Database.add`, consider::

            >>> d = db.add('directory', parent=root, name='foo')
            >>> db.update(d, name='bar')
            >>> d = db.get(d)   # Reload changes
            >>> d['name']
            'bar'


        .. warning::
           When updating an attribute associated with an inverted index, all
           terms for that inverted index in the object need to be rescored.
           For special attributes with the same name as inverted indexes, it's
           the caller's responsibility to ensure terms are passed back during
           update.

           In the email example from :meth:`register_object_type_attrs`, if the
           subject attribute is updated by itself, any previously indexed terms
           passed to the keywords attribute (the message body) would be
           discarded after the update.  If updating the subject, the caller
           would be required to pass the message body in the keywords attribute
           again, in order to preserve those terms.

           If none of the attributes being updated are associated with an
           inverted index that also has a same-named special attribute then
           this warning doesn't apply as the inverted index does not need
           to be updated.
        """
        if self._readonly:
            raise DatabaseReadOnlyError('upgrade_to_py3() must be called before database can be modified')
        object_type, object_id = self._to_obj_tuple(obj)

        type_attrs = self._get_type_attrs(object_type)
        get_pickle = False

        # Determine which inverted indexes need to be regenerated for this
        # object.  Builds a dictionary of ivtidxes with a dirty flag and
        # a list of sql columns needed for reindexing.
        ivtidx_columns = {}
        for name, (attr_type, flags, attr_ivtidx, attr_split) in type_attrs.items():
            if flags & ATTR_INVERTED_INDEX:
                if attr_ivtidx not in ivtidx_columns:
                    ivtidx_columns[attr_ivtidx] = [ False, [] ]
                if flags & ATTR_SEARCHABLE:
                    ivtidx_columns[attr_ivtidx][1].append(name)
                if flags & (ATTR_SIMPLE | ATTR_IGNORE_CASE):
                    get_pickle = True
                if name in attrs:
                    ivtidx_columns[attr_ivtidx][0] = True

            # If the updated attribute is stored in the pickle (either a simple attr
            # or an case-insensitive indexed attr in which __foo is in the pickle)
            # then we must first retrieve the pickle for this object from the db.
            if (flags & ATTR_SIMPLE or flags & ATTR_INDEXED_IGNORE_CASE == ATTR_INDEXED_IGNORE_CASE) and \
               name in attrs:
                get_pickle = True

        # TODO: if ObjectRow is supplied, don't need to fetch columns
        # that are available in the ObjectRow.  (Of course this assumes
        # the object wasn't changed via elsewhere during the life of the
        # ObjectRow object, so maybe we don't want to do that.)
        reqd_columns = ['pickle'] if get_pickle else []
        for dirty, searchable_attrs in ivtidx_columns.values():
            if dirty:
                reqd_columns.extend(searchable_attrs)

        if reqd_columns:
            q = 'SELECT %s FROM objects_%s WHERE id=?' % (','.join(reqd_columns), object_type)
            row = self._db_query_row(q, (object_id,))
            if not row:
                raise ValueError, "Can't update unknown object (%s, %d)" % (object_type, object_id)
            if reqd_columns[0] == 'pickle' and row[0]:
                # One of the attrs we're updating is in the pickle, so we
                # have fetched it; now convert it to a dict.
                row_attrs = dbunpickle(row[0])
                for key, value in row_attrs.items():
                    # Rename all __foo to foo for ATTR_IGNORE_CASE columns
                    if key.startswith('__') and type_attrs[key[2:]][1] & ATTR_IGNORE_CASE:
                        row_attrs[key[2:]] = value
                        del row_attrs[key]
                # Update stored pickle data with new ATTR_SIMPLE attribute values
                row_attrs.update(attrs)
                attrs = row_attrs


        if parent:
            attrs['parent_type'], attrs['parent_id'] = self._to_obj_tuple(parent, numeric=True)
        attrs['id'] = object_id
        # Make copy of attrs for later query, since we're now about to mess with it.
        orig_attrs = attrs.copy()

        # Merge the ivtidx columns we grabbed above into attrs dict.
        for n, name in enumerate(reqd_columns):
            if name not in attrs and name != 'pickle':
                attrs[name] = row[n]

        for ivtidx, (dirty, searchable_attrs) in ivtidx_columns.items():
            if not dirty:
                # No attribute for this ivtidx changed.
                continue
            split = self._inverted_indexes[ivtidx]['split']
            # Remove existing indexed words for this object.
            self._delete_object_inverted_index_terms((object_type, object_id), ivtidx)

            # TODO: code duplication from add()
            # Need to reindex all columns in this object using this ivtidx.
            terms_list = []
            for name, (attr_type, flags, attr_ivtidx, attr_split) in type_attrs.items():
                if attr_ivtidx == ivtidx and name in attrs:
                    if attr_type == BYTES_TYPE and isinstance(attrs[name], RAW_TYPE):
                        # We store string objects in the db as buffers, in
                        # order to prevent any unicode issues.  So we need
                        # to convert the buffer we got from the db back to
                        # a string before parsing the attribute into terms.
                        attrs[name] = BYTES_TYPE(attrs[name])
                    terms_list.append((attrs[name], 1.0, attr_split or split, ivtidx))

            if ivtidx in attrs and ivtidx not in type_attrs:
                # Attribute named after an inverted index is given, but
                # that ivtidx is not a named attribute (which would be handled
                # in the for loop just above).
                terms_list.append((attrs[ivtidx], 1.0, split, ivtidx))

            terms = self._score_terms(terms_list)
            self._add_object_inverted_index_terms((object_type, object_id), ivtidx, terms)
            if ivtidx in type_attrs:
                # Registered attribute named after ivtidx; store ivtidx
                # terms in object.
                if not terms and ivtidx in orig_attrs:
                    # Update removed all terms for this ivtidx, remove from pickle.
                    orig_attrs[ivtidx] = None
                elif terms:
                    # There are terms for this ivtidx, store in pickle.
                    orig_attrs[ivtidx] = terms.keys()

        query, values = self._make_query_from_attrs("update", orig_attrs, object_type)
        self._db_query(query, values)
        self._set_dirty()
        # TODO: if an objectrow was given, return an updated objectrow


    def commit(self):
        """
        Explicitly commit any changes made to the database.

        .. note:: Any uncommitted changes will automatically be committed at
                  program exit.
        """
        main.signals['exit'].disconnect(self.commit)
        self._dirty = False
        with self._lock:
            self._db.commit()


    def query(self, **attrs):
        """
        Query the database for objects matching all of the given keyword
        attributes.

        Keyword arguments can be any previously registered :attr:`~kaa.db.ATTR_SEARCHABLE`
        object attribute for any object type, or the name of a registered
        inverted index.  There are some special keyword arguments:

        :param parent: require all matched objects to have the given object
                       (or objects) as their immediate parent ancestor.  If
                       parent is a list or tuple, then they specify a list
                       of possible parents, any of which would do.
        :type parent: :class:`ObjectRow`, 2-tuple (object_type, object_id), 2-tuple
                      (object_type, :class:`~kaa.db.QExpr`), or a list of those
        :param object: match only a specific object. Not usually very useful,
                       but could be used to test if the given object matches
                       terms from an inverted index.
        :type object: :class:`ObjectRow` or 2-tuple (object_type, object_id)
        :param type: only search items of this object type; if None (or not
                     specified) then all types are searched
        :type type: str
        :param limit: return only this number of results; if None (or not
                      specified), all matches are returned.
        :type limit: int
        :param attrs: a list of attribute names to be returned; if not specified,
                      all attributes registered with the object type are available
                      in the result.  Only specifying the attributes required
                      can help performance moderately, but generally it isn't
                      required except wit *distinct* below.
        :type attrs: list of str
        :param distinct: if True, ensures that each object in the result set is
                         unique with respect to the attributes specified in the
                         *attrs* parameter.  When distinct is True, *attrs* is
                         required and none of the attributes specified may be
                         simple.
        :param orattrs: attribute names that will be ORed in the query; by default,
                        all attributes are ANDed.
        :type orattrs: list
        :raises: ValueError if the query is invalid (e.g. attempting to query
                 on a simple attribute)
        :returns: a list of :class:`ObjectRow` objects

        When any of the attributes are inverted indexes, the result list is
        sorted according to a score.  The score is based upon the frequency
        of the matched terms relative to the entire database.

        .. note:: If you know which type of object you're interested in, you
           should specify the *type* as it will help improve performance by
           reducing the scope of the search, especially for inverted indexes.

           Another significant factor in performance is whether or not a *limit*
           is specified.  Query time generally scales linearly with respect to
           the number of rows found, but in the case of searches on inverted
           indexes, specifying a limit can drastically reduce search time, but
           does not affect scoring.

        Values supplied to attributes (other than inverted indexes) require
        exact matches.  To search based on an expression, such as inequality,
        ranges, substrings, set inclusion, etc. require the use of a
        :class:`~kaa.db.QExpr` object.

        Expanding on the example provided in
        :meth:`~kaa.db.Database.register_object_type_attrs`::

            >>> db.add('msg', sender=u'Stewie Griffin', subject=u'Blast!',
                       keywords='When the world is mine, your death shall be quick and painless.')
            >>> # Exact match based on sender
            >>> db.query(sender=u'Stewie Griffin')
            [<kaa.db.ObjectRow object at 0x7f652b251030>]
            >>> # Keyword search requires all keywords
            >>> db.query(keywords=['death', 'blast'])
            [<kaa.db.ObjectRow object at 0x7f652c3d1f90>]
            >>> # This doesn't work, since it does an exact match ...
            >>> db.query(sender=u'Stewie')
            []
            >>> # ... but we can use QExpr to do a substring/pattern match.
            >>> db.query(sender=QExpr('like', u'Stewie%'))
            [<kaa.db.ObjectRow object at 0x7f652c3d1f90>]
            >>> # How about a regexp search.
            >>> db.query(sender=QExpr('regexp', ur'.*\\bGriffin'))
            [<kaa.db.ObjectRow object at 0x7f652b255030>]

        """
        query_info = {}
        parents = []
        query_type = "ALL"
        results = []
        query_info["columns"] = {}
        query_info["attrs"] = {}

        if "object" in attrs:
            attrs['type'], attrs['id'] = self._to_obj_tuple(attrs['object'])
            del attrs['object']

        ivtidx_results = ivtidx_results_by_type = None
        for ivtidx in self._inverted_indexes:
            # TODO: Possible optimization: do ivtidx search after the query
            # below only on types that have results iff all queried columns are
            # indexed.
            # TODO: could be smarter about the order in which we do ivtidx
            # searches (do least populated first)
            if ivtidx in attrs:
                # If search criteria other than this inverted index are specified,
                # we can't enforce a limit on the search, otherwise we
                # might miss intersections.
                if len(set(attrs).difference(('type', 'limit', ivtidx))) > 0:
                    limit = None
                else:
                    limit = attrs.get('limit')

                r = self._query_inverted_index(ivtidx, attrs[ivtidx], limit, attrs.get('type'))
                if ivtidx_results is None:
                    ivtidx_results = r
                else:
                    for o in ivtidx_results.keys():
                        if o not in r:
                            del ivtidx_results[o]
                        else:
                            ivtidx_results[o] *= r[o]

                if not ivtidx_results:
                    # No matches, so we're done.
                    return []

                del attrs[ivtidx]

        if ivtidx_results:
            ivtidx_results_by_type = {}
            for tp, id in ivtidx_results.keys():
                if tp not in ivtidx_results_by_type:
                    ivtidx_results_by_type[tp] = []
                ivtidx_results_by_type[tp].append(id)

        if attrs.get('type') is not None:
            if attrs["type"] not in self._object_types:
                raise ValueError, "Unknown object type '%s'" % attrs["type"]
            type_list = [(attrs["type"], self._object_types[attrs["type"]])]
        else:
            type_list = self._object_types.items()

        if attrs.get('parent') is not None:
            # ("type", id_or_QExpr) or (("type1", id_or_QExpr), ("type2", id_or_QExpr), ...)
            if isinstance(attrs['parent'], ObjectRow) or \
               (isinstance(attrs['parent'], (list, tuple)) and \
                not isinstance(attrs['parent'][0], (list, tuple))):
                # (type, parent) -> ((type, parent),)
                attrs['parent'] = (attrs['parent'],)

            for parent_obj in attrs['parent']:
                parent_type_id, parent_id = self._to_obj_tuple(parent_obj, numeric=True)
                if not isinstance(parent_id, QExpr):
                    parent_id = QExpr("=", parent_id)
                parents.append((parent_type_id, parent_id))

        if attrs.get('limit') is not None:
            result_limit = attrs["limit"]
        else:
            result_limit = None

        if attrs.get('attrs') is not None:
            requested_columns = attrs["attrs"]
        else:
            requested_columns = None

        if attrs.get('distinct') is not None:
            if attrs["distinct"]:
                if not requested_columns:
                    raise ValueError, "Distinct query specified, but no attrs kwarg given."
                query_type = "DISTINCT"

        if attrs.get('orattrs') is not None:
            orattrs = set(attrs['orattrs'])
        else:
            orattrs = ()

        # Remove all special keywords
        for attr in ('parent', 'object', 'type', 'limit', 'attrs', 'distinct', 'orattrs'):
            attrs.pop(attr, None)

        for type_name, (type_id, type_attrs, type_idx) in type_list:
            if ivtidx_results and type_id not in ivtidx_results_by_type:
                # If we've done a ivtidx search, don't bother querying
                # object types for which there were no hits.
                continue

            # Select only sql columns (i.e. attrs that aren't ATTR_SIMPLE).
            all_columns = [ x for x in type_attrs if type_attrs[x][1] & ATTR_SEARCHABLE ]
            if requested_columns:
                columns = requested_columns[:]
                # Ensure that all the requested columns exist for this type
                missing = tuple(set(columns).difference(type_attrs.keys()))
                if missing:
                    raise ValueError, "One or more requested attributes %s are not available for type '%s'" % \
                                      (str(missing), type_name)
                # If any of the requested attributes are ATTR_SIMPLE or
                # ATTR_INDEXED_IGNORE_CASE then we need the pickle.
                pickled = [ x for x in columns if type_attrs[x][1] & (ATTR_SIMPLE | ATTR_INDEXED_IGNORE_CASE) in
                                                                     (ATTR_SIMPLE, ATTR_INDEXED_IGNORE_CASE)]
                if pickled:
                    # One or more attributes from pickle are requested in attrs list,
                    # so we need to grab the pickle column.
                    if 'pickle' not in columns:
                        columns.append('pickle')
                    # Remove the list of pickled attributes so we don't
                    # request them as sql columns.
                    columns = list(set(columns).difference(pickled))
            else:
                columns = all_columns

            # Now construct a query based on the supplied attributes for this
            # object type.

            # If any of the attribute names aren't valid for this type, then we
            # don't bother matching, since this an AND query and there won't be
            # any matches.
            missing = set(attrs).difference(all_columns)
            if missing:
                # Raise exception if user attempts to search on a simple attr.
                simple = [ x for x in missing if x in type_attrs and type_attrs[x][1] & ATTR_SIMPLE ]
                if simple:
                    raise ValueError, "Querying on non-searchable attribute '%s'" % simple[0]
                continue

            q, qor = [], []
            query_values, qor_values = [], []
            q.append("SELECT %s '%s',%d,id,%s FROM objects_%s" % \
                (query_type, type_name, type_id, ",".join(columns), type_name))

            if ivtidx_results != None:
                q.append("WHERE")
                q.append("id IN %s" % _list_to_printable(ivtidx_results_by_type[type_id]))

            if len(parents):
                q.append(("WHERE", "AND")["WHERE" in q])
                expr = []
                for parent_type, parent_id in parents:
                    sql, values = parent_id.as_sql("parent_id")
                    expr.append("(parent_type=? AND %s)" % sql)
                    query_values += (parent_type,) + values
                q.append("(%s)" % " OR ".join(expr))

            for attr, value in attrs.items():
                is_or_attr = attr in orattrs
                attr_type, attr_flags = type_attrs[attr][:2]
                if not isinstance(value, QExpr):
                    value = QExpr("=", value)

                # Coerce between numeric types; also coerce a string of digits into a numeric
                # type.
                if attr_type in (int, long, float) and (isinstance(value._operand, (int, long, float)) or \
                    isinstance(value._operand, basestring) and value._operand.isdigit()):
                    value._operand = attr_type(value._operand)

                # Verify expression operand type is correct for this attribute.
                if value._operator not in ("range", "in", "not in") and \
                   not isinstance(value._operand, attr_type):
                    raise TypeError, "Type mismatch in query: '%s' (%s) is not a %s" % \
                                          (str(value._operand), str(type(value._operand)), str(attr_type))

                # Queries on ATTR_IGNORE_CASE string columns are case-insensitive.
                if isinstance(value._operand, basestring) and type_attrs[attr][1] & ATTR_IGNORE_CASE:
                    value._operand = value._operand.lower()
                    if not (type_attrs[attr][1] & ATTR_INDEXED):
                        # If this column is ATTR_INDEXED then we already ensure
                        # the values are stored in lowercase in the db, so we
                        # don't want to get sql to lower() the column because
                        # it's needless, and more importantly, we won't be able
                        # to use any indices on the column.
                        attr = 'lower(%s)' % attr

                if isinstance(value._operand, BYTES_TYPE):
                    # For Python 2, convert non-unicode strings to buffers.  (For Python 3,
                    # BYTES_TYPE == RAW_TYPE so this is a no-op.)
                    value._operand = RAW_TYPE(value._operand)

                sql, values = value.as_sql(attr)
                if is_or_attr:
                    qor.append(sql)
                    qor_values.extend(values)
                else:
                    q.append('AND' if 'WHERE' in q else 'WHERE')
                    q.append(sql)
                    query_values.extend(values)

            if qor:
                q.append('AND' if 'WHERE' in q else 'WHERE')
                q.append('(%s)' % ' OR '.join(qor))

            if query_type == 'DISTINCT':
                q.append(' GROUP BY %s' % ','.join(requested_columns))

            if result_limit != None:
                q.append(" LIMIT %d" % result_limit)

            q = " ".join(q)
            rows = self._db_query(q, query_values + qor_values, cursor=self._qcursor)

            if result_limit != None:
                results.extend(rows[:result_limit - len(results) + 1])
            else:
                results.extend(rows)

            query_info["columns"][type_name] = ["type"] + columns
            query_info["attrs"][type_name] = type_attrs

            if result_limit != None and len(rows) == result_limit:
                # No need to try the other types, we're done.
                break

        # If ivtidx search was done, sort results based on score (highest
        # score first).
        if ivtidx_results:
            results.sort(key=lambda r: ivtidx_results[(r[1], r[2])])

        return results


    def query_one(self, **attrs):
        """
        Like :meth:`~kaa.db.Database.query` but returns a single object only.

        This is a convenience method, and query_one(...) is equivalent to::

            results = db.query(...)
            if results:
                obj = results[0]
            else:
                obj = None

        limit=1 is implied by this query.
        """
        results = self.query(limit=1, **attrs)
        return results[0] if results else None


    def _score_terms(self, terms_list):
        """
        Scores the terms given in terms_list, which is a list of tuples (terms,
        coeff, split, ivtidx), where terms is the string or sequence of
        terms to be scored, coeff is the weight to give each term in this part
        (1.0 is normal), split is the function or regular expression used to
        split terms (only used if a string is given for terms), and ivtidx is
        the name of inverted index we're scoring for.

        Terms are either unicode objects or strings, or sequences of unicode or
        string objects.  In the case of strings, they are passed through
        py3_str() to try to decode them intelligently.

        Each term T is given the score:
             sqrt( (T coeff * T count) / total term count )

        Counts are relative to the given object, not all objects in the
        database.

        Returns a dict of term->score.  Terms (the keys) are converted to
        unicode objects, but their case is preserved as given (if term is
        given more than once, the case of the first occurence is used), and
        score (the values) are calculated as described above.
        """
        terms_scores = {}
        total_terms = 0

        for terms, coeff, split, ivtidx in terms_list:
            if not terms:
                continue
            # Swap ivtidx name for inverted index definition dict
            ivtidx = self._inverted_indexes[ivtidx]
            if not isinstance(terms, (basestring, list, tuple)):
                raise ValueError, "Invalid type (%s) for ATTR_INVERTED_INDEX attribute. " \
                                  "Only sequence, unicode or str allowed." % str(type(terms))

            if isinstance(terms, (list, tuple)):
                terms = [py3_str(term) for term in terms]
                parsed = terms
            else:
                terms = py3_str(terms)
                if callable(split):
                    parsed = list(split(terms))
                else:
                    parsed = split.split(terms)

            for term in parsed:
                if not term or (ivtidx['max'] and len(term) > ivtidx['max']) or \
                   (ivtidx['min'] and len(term) < ivtidx['min']):
                    continue

                lower_term = term.lower()

                if ivtidx['ignore'] and lower_term in ivtidx['ignore']:
                    continue
                if lower_term not in terms_scores:
                    terms_scores[lower_term] = [term, coeff]
                else:
                    terms_scores[lower_term][1] += coeff
                total_terms += 1

        # Score based on term frequency in document.  (Add weight for
        # non-dictionary terms?  Or longer terms?)
        for lower_term, score in terms_scores.items():
            terms_scores[lower_term][1] = math.sqrt(terms_scores[lower_term][1] / total_terms)
        return dict(terms_scores.values())


    def _delete_object_inverted_index_terms(self, (object_type, object_id), ivtidx):
        """
        Removes all indexed terms under the specified inverted index for the
        given object.  This function must be called when an object is removed
        from the database, or when an ATTR_INVERTED_INDEX attribute of an
        object is being updated (and therefore that inverted index must be
        re-indexed).
        """
        self._delete_multiple_objects_inverted_index_terms({object_type: ((ivtidx,), (object_id,))})


    def _delete_multiple_objects_inverted_index_terms(self, objects):
        """
        objects = dict type_name -> (ivtidx tuple, ids tuple)
        """
        for type_name, (ivtidxes, object_ids) in objects.items():
            # Resolve object type name to id
            type_id = self._get_type_id(type_name)

            for ivtidx in ivtidxes:
                # Remove all terms for the inverted index associated with this
                # object.  A trigger will decrement the count column in the
                # terms table for all term_id that get affected.
                self._db_query("DELETE FROM ivtidx_%s_terms_map WHERE object_type=? AND object_id IN %s" % \
                               (ivtidx, _list_to_printable(object_ids)), (type_id,))
                self._inverted_indexes[ivtidx]['objectcount'] -= len(object_ids)


    def _add_object_inverted_index_terms(self, (object_type, object_id), ivtidx, terms):
        """
        Adds the dictionary of terms (as computed by _score_terms()) to the
        specified inverted index database for the given object.
        """
        if not terms:
            return

        # Resolve object type name to id
        object_type = self._get_type_id(object_type)

        # Holds any of the given terms that already exist in the database
        # with their id and count.
        db_terms_count = {}

        terms_list = _list_to_printable([ t.lower() for t in terms.keys() ])
        q = "SELECT id,term,count FROM ivtidx_%s_terms WHERE term IN %s" % (ivtidx, terms_list)
        rows = self._db_query(q)
        for row in rows:
            db_terms_count[row[1]] = row[0], row[2]

        # For executemany queries later.
        update_list, map_list = [], []

        for term, score in terms.items():
            term = term.lower()
            if term not in db_terms_count:
                # New term, so insert it now.
                self._db_query('INSERT OR REPLACE INTO ivtidx_%s_terms VALUES(NULL, ?, 1)' % ivtidx, (term,))
                db_id, db_count = self._cursor.lastrowid, 1
                db_terms_count[term] = db_id, db_count
            else:
                db_id, db_count = db_terms_count[term]
                update_list.append((db_count + 1, db_id))

            map_list.append((int(score*10), db_id, object_type, object_id, score))

        self._db_query('UPDATE ivtidx_%s_terms SET count=? WHERE id=?' % ivtidx, update_list, many = True)
        self._db_query('INSERT INTO ivtidx_%s_terms_map VALUES(?, ?, ?, ?, ?)' % ivtidx, map_list, many = True)


    def _query_inverted_index(self, ivtidx, terms, limit = 100, object_type = None):
        """
        Queries the inverted index ivtidx for the terms supplied in the terms
        argument.  If terms is a string, it is parsed into individual terms
        based on the split for the given ivtidx.  The terms argument may
        also be a list or tuple, in which case no parsing is done.

        The search algorithm tries to optimize for the common case.  When
        terms are scored (_score_terms()), each term is assigned a score that
        is stored in the database (as a float) and also as an integer in the
        range 0-10, called rank.  (So a term with score 0.35 has a rank 3.)

        Multiple passes are made over the terms map table for the given ivtidx,
        first starting at the highest rank fetching a certain number of rows,
        and progressively drilling down to lower ranks, trying to find enough
        results to fill our limit that intersects on all supplied terms.  If
        our limit isn't met and all ranks have been searched but there are
        still more possible matches (because we use LIMIT on the SQL
        statement), we expand the LIMIT (currently by an order of 10) and try
        again, specifying an OFFSET in the query.

        The worst case scenario is given two search terms, each term matches
        50% of all rows but there is only one intersecting row.  (Or, more
        generally, given N terms, each term matches (1/N)*100 percent rows with
        only 1 row intersection between all N terms.)   This could be improved
        by avoiding the OFFSET/LIMIT technique as described above, but that
        approach provides a big performance win in more common cases.  This
        case can be mitigated by caching common term combinations, but it is
        an extremely difficult problem to solve.

        object_type specifies an type name to search (for example we can
        search type "image" with keywords "2005 vacation"), or if object_type
        is None (default), then all types are searched.

        This function returns a dictionary (object_type, object_id) -> score
        which match the query.
        """
        t0 = time.time()
        # Fetch number of files the inverted index applies to.  (Used in score
        # calculations.)
        objectcount = self._inverted_indexes[ivtidx]['objectcount']

        if not isinstance(terms, (list, tuple)):
            split = self._inverted_indexes[ivtidx]['split']
            if callable(split):
                terms = [term for term in split(py3_str(terms).lower()) if term]
            else:
                terms = [term for term in split.split(py3_str(terms).lower()) if term]
        else:
            terms = [ py3_str(x).lower() for x in terms ]

        # Remove terms that aren't indexed (words less than minimum length
        # or and terms in the ignore list for this ivtidx).
        if self._inverted_indexes[ivtidx]['min']:
            terms = [ x for x in terms if len(x) >= self._inverted_indexes[ivtidx]['min'] ]
        if self._inverted_indexes[ivtidx]['ignore']:
            terms = [ x for x in terms if x not in self._inverted_indexes[ivtidx]['ignore'] ]

        terms_list = _list_to_printable(terms)
        nterms = len(terms)

        if nterms == 0:
            return []

        # Find term ids and order by least popular to most popular.
        rows = self._db_query('SELECT id,term,count FROM ivtidx_%s_terms WHERE ' \
                              'term IN %s ORDER BY count' % (ivtidx, terms_list))
        save = map(lambda x: x.lower(), terms)
        terms = {}
        ids = []
        for row in rows:
            if row[2] == 0:
                return []

            # Give terms weight according to their order
            order_weight = 1 + len(save) - list(save).index(row[1])
            terms[row[0]] = {
                'term': row[1],
                'count': row[2],
                'idf_t': math.log(objectcount / row[2] + 1) + order_weight,
                'ids': {}
            }
            ids.append(row[0])

        # Not all the terms we requested are in the database, so we return
        # 0 results.
        if len(ids) < nterms:
            return []

        if object_type:
            # Resolve object type name to id
            object_type = self._get_type_id(object_type)

        results, state = {}, {}
        for id in ids:
            results[id] = {}
            state[id] = {
                'offset': [0]*11,
                'more': [True]*11,
                'count': 0,
                'done': False
            }

        all_results = {}
        if limit == None:
            limit = objectcount

        if limit <= 0 or objectcount <= 0:
            return {}

        sql_limit = min(limit*3, 200)
        finished = False
        nqueries = 0

        # Keep a dict keyed on object_id that we can use to narrow queries
        # once we have a full list of all objects that match a given term.
        id_constraints = None
        t1 = time.time()
        while not finished:
            for rank in range(10, -1, -1):
                for id in ids:
                    if not state[id]['more'][rank] or state[id]['done']:
                        # If there's no more results at this rank, or we know
                        # we've already seen all the results for this term, we
                        # don't bother with the query.
                        continue

                    q = 'SELECT object_type,object_id,frequency FROM ivtidx_%s_terms_map ' % ivtidx + \
                        'WHERE term_id=? AND rank=? %s %%s LIMIT ? OFFSET ?'

                    if object_type == None:
                        q %= ''
                        v = [id, rank, sql_limit, state[id]["offset"][rank]]
                    else:
                        q %= 'AND object_type=?'
                        v = [id, rank, object_type, sql_limit, state[id]["offset"][rank]]

                    if id_constraints:
                        # We know about all objects that match one or more of the other
                        # search terms, so we add the constraint that all rows for this
                        # term match the others as well.  Effectively we push the logic
                        # to generate the intersection into the db.
                        # XXX: This can't benefit from the index if object_type
                        # is not specified.
                        q %= ' AND object_id IN %s' % _list_to_printable(tuple(id_constraints))
                        # But since we're specifying a list of ids to search for with this
                        # term, we can't use limit/offset, since the constraints might be
                        # different since the last iteration.
                        v[-2:] = [-1, 0]
                    else:
                        q %= ''

                    rows = self._db_query(q, v)
                    nqueries += 1
                    state[id]['more'][rank] = len(rows) == sql_limit
                    state[id]['count'] += len(rows)

                    for row in rows:
                        results[id][row[0], row[1]] = row[2] * terms[id]['idf_t']
                        terms[id]['ids'][row[1]] = 1

                    if state[id]['count'] >= terms[id]['count'] or \
                       (id_constraints and len(rows) == len(id_constraints)):
                        # If we've now retrieved all objects for this term, or if
                        # all the results we just got now intersect with our
                        # constraints set, we're done this term and don't bother
                        # querying it at other ranks.
                        #print "Done term '%s' at rank %d" % (terms[id]['term'], rank)
                        state[id]['done'] = True
                        if id_constraints is not None:
                            id_constraints = id_constraints.intersection(terms[id]['ids'])
                        else:
                            id_constraints = set(terms[id]['ids'])
                #
                # end loop over terms


                for r in reduce(lambda a, b: set(a).intersection(b), results.values()):
                    all_results[r] = 0
                    for id in ids:
                        if r in results[id]:
                            all_results[r] += results[id][r]

                # If we have enough results already, no sense in querying the
                # next rank.
                if limit > 0 and len(all_results) > limit*2:
                    finished = True
                    #print "Breaking at rank:", rank
                    break
            #
            # end loop over ranks

            if finished:
                break

            finished = True
            for index in range(len(ids)):
                id = ids[index]

                if index > 0:
                    last_id = ids[index-1]
                    a = results[last_id]
                    b = results[id]
                    intersect = set(a).intersection(b)

                    if len(intersect) == 0:
                        # Is there any more at any rank?
                        a_more = b_more = False
                        for rank in range(11):
                            a_more = a_more or state[last_id]['more'][rank]
                            b_more = b_more or state[id]['more'][rank]

                        if not a_more and not b_more:
                            # There's no intersection between these two search
                            # terms and neither have more at any rank, so we
                            # can stop the whole query.
                            finished = True
                            break

                # There's still hope of a match.  Go through this term and
                # see if more exists at any rank, increasing offset and
                # unsetting finished flag so we iterate again.
                for rank in range(10, -1, -1):
                    if state[id]['more'][rank] and not state[id]['done']:
                        state[id]['offset'][rank] += sql_limit
                        finished = False

            # If we haven't found enough results after this pass, grow our
            # limit so that we expand our search scope.  (XXX: this value may
            # need empirical tweaking.)
            sql_limit *= 10

        # end loop while not finished
        log.info('%d results, did %d subqueries, %.04f seconds (%.04f overhead)',
                 len(all_results), nqueries, time.time()-t0, t1-t0)
        return all_results


    def get_inverted_index_terms(self, ivtidx, associated = None, prefix = None):
        """
        Obtain terms used by objects for an inverted index.

        :param ivtidx: the name of an inverted index previously registered with
                       :meth:`~kaa.db.Database.register_inverted_index`.
        :type ivtidx: str
        :param associated: specifies a list of terms, and only those terms which are
                           mapped to objects *in addition to* the supplied associated
                           terms will be returned.  If None, all terms for the inverted
                           index are returned.
        :type associated: list of str or unicode
        :param prefix: only terms that begin with the specified prefix are returned.
                       This is useful for auto-completion while a user is typing a
                       query.
        :type prefix: str or unicode
        :returns: a list of 2-tuples, where each tuple is (*term*, *count*).  If
                  *associated* is not given, *count* is the total number of objects
                  that term is mapped to.  Otherwise, *count* reflects the number
                  of objects which have that term plus all the given associated
                  terms.  The list is sorted with the highest counts appearing first.

        For example, given an otherwise empty database, if you have an object
        with terms ['vacation', 'hawaii'] and two other object with terms
        ['vacation', 'spain'] and the associated list passed is ['vacation'],
        the return value will be [('spain', 2), ('hawaii', 1)].
        """
        if ivtidx not in self._inverted_indexes:
            raise ValueError, "'%s' is not a registered inverted index." % ivtidx

        if prefix:
            where_clause = 'WHERE terms.term >= ? AND terms.term <= ?'
            where_values = (prefix, prefix + 'z')
        else:
            where_clause = ''
            where_values = ()

        if not associated:
            return self._db_query('''SELECT term, count
                                      FROM ivtidx_%s_terms AS terms
                                        %s
                                  ORDER BY count DESC''' % (ivtidx, where_clause), where_values)


        rows = self._db_query('SELECT id FROM ivtidx_%s_terms WHERE term IN %s ORDER BY count' % \
                              (ivtidx, _list_to_printable(associated)))
        term_ids = [ x[0] for x in rows ]
        if len(term_ids) < len(associated):
            return []

        query = '''SELECT term, COUNT(*) AS total
                     FROM ivtidx_%s_terms_map AS t0''' % ivtidx
        for n, term_id in enumerate(term_ids):
            query += ''' JOIN ivtidx_%s_terms_map t%d
                           ON t%d.object_type = t%d.object_type AND
                              t%d.object_id = t%d.object_id AND
                              t%d.term_id = %d''' % \
                     (ivtidx, n + 1, n, n + 1, n, n + 1, n + 1, term_id)
        query += ''' JOIN ivtidx_%s_terms AS terms
                       ON t0.term_id = terms.id AND
                          t0.term_id NOT IN %s
                       %s
                 GROUP BY t0.term_id
                 ORDER BY total DESC ''' % \
                 (ivtidx, _list_to_printable(term_ids), where_clause)
        return self._db_query(query, where_values)


    def get_db_info(self):
        """
        Return information about the database.

        :returns: a dict

        The returned dictionary has the following keys:
            * count: dict of object types holding their counts
            * total: total number of objects in the database
            * types: a dict keyed on object type which contains:
                * attrs: a dictionary of registered attributes for this type
                * idx: a list of composite indexes for this type
            * termcounts: a dict of the number of indexed terms for each
              inverted index
            * file: full path to the database file
        """
        total = 0
        info = {
            'count': {},
            'types': {}
        }
        for name in self._object_types:
            id, attrs, idx = self._object_types[name]
            info['types'][name] = {
                'attrs': attrs,
                'idx': idx
            }
            row = self._db_query_row('SELECT COUNT(*) FROM objects_%s' % name)
            info['count'][name] = row[0]
            total += row[0]

        info['total'] = total

        info['termcounts'] = {}
        for ivtidx in self._inverted_indexes:
            row = self._db_query_row('SELECT COUNT(*) FROM ivtidx_%s_terms' % ivtidx)
            info['termcounts'][ivtidx] = int(row[0])

        info['file'] = self._dbfile
        return info


    def set_metadata(self, key, value):
        """
        Associate simple key/value pairs with the database.

        :param key: the key name for the metadata; it is required that key
                    is prefixed with ``appname::`` in order to avoid namespace
                    collisions.
        :type key: str or unicode
        :param value: the value to associate with the given key
        :type value: str or unicode
        """
        if '::' not in key:
            raise ValueError('Invalid key %s; must be prefixed with "appname::"' % key)

        self._db_query('DELETE FROM meta WHERE attr=?', (key,))
        self._db_query('INSERT INTO meta VALUES (?, ?)', (key, value))
        self._set_dirty()


    def get_metadata(self, key, default=None):
        """
        Fetch metadata previously set by :meth:`~kaa.db.Database.set_metadata`.

        :param key: the key name for the metadata, prefixed with ``appname::``.
        :type key: str
        :param default: value to return if key is not found
        :returns: unicode string containing the value for this key, or
                  the ``default`` parameter if the key was not found.
        """
        row = self._db_query_row('SELECT value FROM meta WHERE attr=?', (key,))
        if row:
            return row[0]
        return default


    def vacuum(self):
        """
        Cleans up the database, removing unused inverted index terms.

        This also calls VACUUM on the underlying sqlite database, which
        rebuilds the database to reclaim unused space and reduces
        fragmentation.

        Applications should call this periodically, however this operation
        can be expensive for large databases so it should be done during
        an extended idle period.
        """
        # We need to do this eventually, but there's no index on count, so
        # this could potentially be slow.  It doesn't hurt to leave rows
        # with count=0, so this could be done intermittently.
        for ivtidx in self._inverted_indexes:
            self._db_query('DELETE FROM ivtidx_%s_terms WHERE count=0' % ivtidx)
        self._db_query("VACUUM")


    @property
    def filename(self):
        """
        Full path to the database file.
        """
        return self._dbfile


    @property
    def lazy_commit(self):
        """
        The interval after which any changes made to the database will be
        automatically committed, or None to require explicit commiting.
        (Default is None.)

        The timer is restarted upon each change to the database, so prolonged
        updates may still benefit from explicit periodic commits.
        """
        return self._lazy_commit_interval

    @lazy_commit.setter
    def lazy_commit(self, value):
        self._lazy_commit_interval = float(value)
        if value is None:
            self._lazy_commit_timer.stop()
        elif self._dirty:
            self._lazy_commit_timer.start(self._lazy_commit_interval)

    @property
    def readonly(self):
        return self._readonly


    def upgrade_to_py3(self):
        raise NotImplementedError
