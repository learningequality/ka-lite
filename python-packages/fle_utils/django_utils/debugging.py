from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist


def validate_via_booleans(handler):
    """
    """
    def tod_wrapper_fn(*args, **kwargs):
        try:
            return handler(*args, **kwargs)
        except ValidationError as ve:
            if settings.DEBUG:
                raise ve
            else:
                return False
    return tod_wrapper_fn
