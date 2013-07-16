# based on: http://www.djangosnippets.org/snippets/1926/
from django.template import Library, Node, TemplateSyntaxError
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson
from django.utils.safestring import mark_safe

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

from django.template import Node, VariableNode
from django.template.loader_tags import BlockNode, ExtendsNode
from django.template.loader import get_template
@register.tag
def include_block(parser, token):
    """ From http://stackoverflow.com/questions/2687173/django-how-can-i-get-a-block-from-a-template
    Usage: {% include_block "template.html" "block_name" %}
    """
    try:
        tag_name, include_file, block_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a two arguments" % (token.contents.split()[0]))

    #pass vars with stripped quotes 
    return IncludeBlockNode(include_file.replace('"', ''), block_name.replace('"', ''))

class IncludeBlockNode(Node):
    def __init__(self, include_file, block_name):
        self.include_file = include_file
        self.block_name = block_name

    def _get_node(self, template, context, name):
        '''
        taken originally from
        http://stackoverflow.com/questions/2687173/django-how-can-i-get-a-block-from-a-template
        '''
        for node in template:
            if isinstance(node, BlockNode) and node.name == name:
                # Note: will not render VariableNode block.super
                return node.nodelist.render(context)
            elif isinstance(node, ExtendsNode):
                return self._get_node(node.nodelist, context, name)
                

        raise Exception("Node '%s' could not be found in template." % name)

    def render(self, context):
        t = get_template(self.include_file)
        return self._get_node(t, context, self.block_name)

@register.filter
def jsonify(object):
    if isinstance(object, QuerySet):
        return serialize('json', object)
    return mark_safe(simplejson.dumps(object))
    
from django import template

from django.template.defaultfilters import floatformat

@register.filter
def percent(value, precision):
  if value is None:
    return None
  return floatformat(value * 100.0, precision) + '%' 