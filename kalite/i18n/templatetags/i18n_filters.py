"""
based on: http://www.djangosnippets.org/snippets/1926/
"""
from django import template
from django.conf import settings
from django.db.models.query import QuerySet
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import floatformat
from django.utils import simplejson
from django.utils.safestring import mark_safe

from .. import get_language_name as i18n_get_language_name


register = Library()

@register.filter
def get_language_name(lang_code):
    return i18n_get_language_name(lang_code)
