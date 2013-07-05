"""
Based on http://stackoverflow.com/questions/2687173/django-how-can-i-get-a-block-from-a-template
"""
from django import template
from django.template import Library, Node, TemplateSyntaxError
from django.template.loader import get_template
from django.template.loader_tags import BlockNode, ExtendsNode
from django.core.serializers import serialize
from django.db.models.query import QuerySet
from django.utils import simplejson


register = Library()


@register.tag
def include_block(parser, token):
    try:
        tag_name, include_file, block_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a two arguments" % (token.contents.split()[0]))

    #pass vars with stripped quotes
    return IncludeBlockNode(include_file.replace('"', ''), block_name.replace('"', ''))

class IncludeBlockNode(template.Node):
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
                return node.nodelist.render(context)
            elif isinstance(node, ExtendsNode):
                return self._get_node(node.nodelist, context, name)

        raise Exception("Node '%s' could not be found in template." % name)

    def render(self, context):
        t = get_template(self.include_file)
        return self._get_node(t, context, self.block_name)