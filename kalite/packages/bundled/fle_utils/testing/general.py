"""
Defines general functions relevant for testing.
"""
import sys
import types

def all_classes_in_module(module_name):
    """
    Returns all classes defined in the given module
    """
    assert sys.version_info >= (2,7)
    import importlib
    module = importlib.import_module(module_name)
    objects = [getattr(module, obj_name) for obj_name in dir(module) if getattr(getattr(module, obj_name), "__module__", "") == module_name]
    classes = filter(lambda obj: isinstance(obj, object) and not isinstance(obj, types.FunctionType), objects)
    return classes