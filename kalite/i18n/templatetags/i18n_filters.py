"""
based on: http://www.djangosnippets.org/snippets/1926/
"""
from django.template import Library

from .. import get_language_name as i18n_get_language_name


register = Library()

@register.filter
def get_language_name(lang_code):
    return i18n_get_language_name(lang_code)
