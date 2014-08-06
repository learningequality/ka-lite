class DynamicSettings(object):
    NAMESPACES = []

    def __init__(self, schema, namespace, source=None):

        # create the namespace inside the class if it doesn't exist yet
        cls = self.__class__
        setattr(cls, namespace, getattr(self, namespace, Namespace()))

        # to make manipulations to the namespace easier
        namespace = self._current_namespace = getattr(cls, namespace)

        # update the namespace schema with what we just got
        namespace._schema.update(schema)

        if source:
            self.add_source(source)

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
