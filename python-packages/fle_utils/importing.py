"""
Contains helper functions for importing modules.
"""

import importlib


def resolve_model(model_path):
    """
    Resolve a full model path into the appropriate import and carry out the import.
    """
    module_path, model_name = model_path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    model = getattr(module, model_name)
    return model