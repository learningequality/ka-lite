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
        setattr(self, namespace, getattr(self, namespace, Namespace()))
        self.NAMESPACES.append(namespace)

        # to make manipulations to the namespace easier
        namespace = self._current_namespace = getattr(self, namespace)
        return namespace

    def add_source(self, source):
        for field in self._current_namespace._schema:
            if field in source:
                setattr(self._current_namespace, field, source[field])

    def is_valid(self):
        return True


class Namespace(object):

    def __init__(self):
        self._schema = {}


class BaseField(object):
    typeclass = None.__class__  # make sure this does not pass

FIELDTYPES = [int, bool, str]

# define all field types
for typ in FIELDTYPES:
    classname = "%sField" % typ.__name__.capitalize()
    globals()[classname] = type(
        classname,
        (BaseField,),
        {'typeclass': typ})
