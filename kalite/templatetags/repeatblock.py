from django import template
from django.template.loader_tags import BlockNode

register = template.Library()


class RepeatBlockNode(template.Node):
    def __init__(self, block):
        self.block = block

    @property
    def nodelist(self):
        return self.block.nodelist

    def render(self, context):
        return self.block.render(context)


@register.tag
def repeatblock(parser, token):
    try:
        tag_name, block_name = token.split_contents()
    except:
        raise template.TemplateSyntaxError('%r tag requires a single argument'
                                           % token.contents.split()[0])
    for nodelist in parser.root_nodelist:
        for block in nodelist.get_nodes_by_type(BlockNode):
            if block.name == block_name:
                return RepeatBlockNode(block)
    raise template.TemplateSyntaxError('%r could not find a previous block '
                                       'named %r' % (tag_name, block_name))