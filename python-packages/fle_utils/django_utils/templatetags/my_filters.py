"""
based on: http://www.djangosnippets.org/snippets/1926/
"""
import json

from django import template
from django.conf import settings
from django.db.models.query import QuerySet
from django.template import Library, Node, TemplateSyntaxError
from django.template.defaultfilters import floatformat
from django.utils.safestring import mark_safe

from fle_utils.django_utils.serializers import serialize
from fle_utils.internet.classes import _dthandler


register = Library()

class RangeNode(Node):
    def __init__(self, parser, range_args, context_name):
        self.template_parser = parser
        self.range_args = range_args
        self.context_name = context_name

    def render(self, context):

        resolved_ranges = []
        for arg in self.range_args:
            compiled_arg = self.template_parser.compile_filter(arg)
            resolved_ranges.append(compiled_arg.resolve(context, ignore_failures=True))
        context[self.context_name] = range(*resolved_ranges)
        return ""


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.tag
def mkrange(parser, token):
    """
    Accepts the same arguments as the 'range' builtin and creates
    a list containing the result of 'range'.

    Syntax:
        {% mkrange [start,] stop[, step] as context_name %}

    For example:
        {% mkrange 5 10 2 as some_range %}
        {% for i in some_range %}
          {{ i }}: Something I want to repeat\n
        {% endfor %}

    Produces:
        5: Something I want to repeat
        7: Something I want to repeat
        9: Something I want to repeat
    """

    tokens = token.split_contents()
    fnctl = tokens.pop(0)

    def error():
        raise TemplateSyntaxError, "%s accepts the syntax: {%% %s [start,] " +\
                "stop[, step] as context_name %%}, where 'start', 'stop' " +\
                "and 'step' must all be integers." %(fnctl, fnctl)

    range_args = []
    while True:
        if len(tokens) < 2:
            error()

        token = tokens.pop(0)

        if token == "as":
            break

        range_args.append(token)

    if len(tokens) != 1:
        error()

    context_name = tokens.pop()

    return RangeNode(parser, range_args, context_name)


@register.filter
def jsonify(object):
    try:
        if isinstance(object, QuerySet):
            return serialize('json', object)
    except:
        pass

    str = mark_safe(json.dumps(object, default=_dthandler))
    if str == "null":
        str = mark_safe("[%s]" % (",".join([json.dumps(o, default=_dthandler) for o in object])))
    return str

@register.filter
def percent(value, precision):
  if value is None:
    return None
  return floatformat(value * 100.0, precision) + '%'


@register.filter
def compute_percent(numerator, denominator, precision=1):
    if not numerator or not denominator:
        return None
    return floatformat((float(numerator) / float(denominator)) * 100, precision) + '%'


@register.filter
def format_name(user, format="first_last"):
    """
    Can be used for objects or dictionaries.
    """
    last_name = getattr(user, "last_name", None) or user.get("last_name", None)
    first_name = getattr(user, "first_name", None) or user.get("first_name", None)
    username = getattr(user, "username", None) or user.get("username", None)

    if format == "first_last":
        # When firstname first, then try to use both, otherwise try firstname, then scramble for anything.
        if last_name and first_name:
            return "%s %s" % (first_name, last_name)
        else:
            return first_name or last_name or username

    elif format == "last_first":
        # When lastname, then try to use both, otherwise try lastname, then scramble for anything.
        if last_name and first_name:
            return "%s, %s" % (last_name, first_name)
        else:
            return last_name or first_name or username

    else:
        raise NotImplementedError("Unrecognized format string: %s" % format)

@register.simple_tag
def central_server_api(path, securesync=False):
    return "%s://%s%s" % ((settings.SECURESYNC_PROTOCOL if securesync else "http"), settings.CENTRAL_SERVER_HOST, path)


@register.assignment_tag
def get_twitter_bootstrap_alert_msg_css_name(tags):
    return 'danger' if tags == 'error' else tags
