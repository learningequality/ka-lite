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

from i18n import get_installed_language_packs

register = Library()

@register.filter
def get_language_name(lang_code, language_choices=None):
    language_choices = language_choices or get_installed_language_packs()

    if not lang_code in language_choices:
        return lang_code
    else:
        return language_choices[lang_code].get("native_name", language_choices[lang_code].get("name", lang_code))
