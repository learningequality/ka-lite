"""
"""
import string

from django.conf import settings
from django.core.exceptions import ValidationError


def verify_raw_password(password, min_length=None):
    min_length = min_length or getattr(settings, "PASSWORD_CONSTRAINTS", {}).get('min_length', 0)

    if len(password) < min_length:
        raise ValidationError("Password should be at least %d characters." % min_length)

    return password
