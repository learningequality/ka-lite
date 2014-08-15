import abc
import json


class DynamicSettings(object):
    NAMESPACES = []

    def __init__(self, namespace=None, schema=None, source=None):
        # start validations

        # cannot have schema or source without a namespace to operate on
        if (schema or source) and not namespace:
            raise Exception('Must have namespace when schema or source is given')

        # end validations

        self.NAMESPACES = []

        if namespace:
            namespace = self.initialize_namespace(namespace)

        # update the namespace schema with what we just got
        if schema:
            namespace._schema.update(schema)

        if source:
            self.add_source(source)

    def __add__(self, other):
        for ns in other.NAMESPACES:
            setattr(self, ns, getattr(other, ns))

        self.NAMESPACES.extend(other.NAMESPACES)

        return self

    def initialize_namespace(self, namespace):
        # create the namespace inside the class if it doesn't exist yet
        setattr(self, namespace, getattr(self, namespace, Namespace(name=namespace)))
        self.NAMESPACES.append(namespace)

        # to make manipulations to the namespace easier
        namespace = self._current_namespace = getattr(self, namespace)
        return namespace

    def add_source(self, source):
        self._current_namespace._source.update(source)
        for field in self._current_namespace._schema:
            if field in source:
                setattr(self._current_namespace, field, source[field])

    def validate(self):
        for nsname in self.NAMESPACES:
            ns = getattr(self, nsname)
            for attrname in ns._source.iterkeys():
                field = ns._schema[attrname]
                field.validate(ns, attrname)

    def to_json(self):
        '''
        Used by JSONEncoder for serializing an object into JSON. Return one
        of the builtin python types serializable into json.
        '''
        return dict((nsname, ns.to_json()) for nsname, ns in self.__dict__.iteritems() if nsname in self.NAMESPACES)


class Namespace(object):

    def __init__(self, name):
        self._schema = {}
        self._source = {}
        self.name = name

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.name

    def to_json(self):
        '''
        Return a dict that's ready for serialization by json.dump/s
        '''
        return dict((attr, val) for attr, val in self.__dict__.iteritems() if attr in self._schema)


class BaseField(object):
    __metaclass__ = abc.ABCMeta

    def _get_typeclass(self):
        return self._typeclass

    def _set_typeclass(self, val):
        self._typeclass = val

    # have to define this on subclasses
    # to be able to instantiate it
    typeclass = abc.abstractproperty(_get_typeclass, _set_typeclass)

    def validate(self, namespace, fieldname):
        val = getattr(namespace, fieldname)
        if val.__class__ != self.typeclass:
            raise ValueError("%s.%s didn't validate with value %s" % (namespace, fieldname, val))


class IntField(BaseField):
    typeclass = int

MISC_FIELDTYPES = [bool, str]

# define all field types
for typ in MISC_FIELDTYPES:
    classname = "%sField" % typ.__name__.capitalize()
    globals()[classname] = type(
        classname,
        (BaseField,),
        {'typeclass': typ})


# NOTE: HACK OF ALL SEASONS INCOMING!  Python's json.JSONEncoder
# class, which the jsonify filter calls, unfortunately doesn't look at
# any of the object's methods unlike repr/str.  So we're gonna do some
# monkey patching to add that functionality.
# taken from:http://stackoverflow.com/questions/18478287/making-object-json-serializable-with-regular-encoder
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)

_default.default = json.JSONEncoder().default  # save unmodified default, which just raises TypeError
json.JSONEncoder.default = _default  # replacement
