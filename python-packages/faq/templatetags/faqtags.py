from __future__ import absolute_import

from django import template
from ..models import Question, Topic

register = template.Library()

class FaqListNode(template.Node):
    def __init__(self, num, varname, topic=None):
        self.num = template.Variable(num)
        self.topic = template.Variable(topic) if topic else None
        self.varname = varname

    def render(self, context):
        try:
            num = self.num.resolve(context)
            topic = self.topic.resolve(context) if self.topic else None
        except template.VariableDoesNotExist:
            return ''
        
        if isinstance(topic, Topic):
            qs = Question.objects.filter(topic=topic)
        elif topic is not None:
            qs = Question.objects.filter(topic__slug=topic)
        else:
            qs = Question.objects.all()
            
        context[self.varname] = qs.filter(status=Question.ACTIVE)[:num]
        return ''

@register.tag
def faqs_for_topic(parser, token):
    """
    Returns a list of 'count' faq's that belong to the given topic
    the supplied topic argument must be in the slug format 'topic-name'
    
    Example usage::
    
        {% faqs_for_topic 5 "my-slug" as faqs %}
    """

    args = token.split_contents()
    if len(args) != 5:
        raise template.TemplateSyntaxError("%s takes exactly four arguments" % args[0])
    if args[3] != 'as':
        raise template.TemplateSyntaxError("third argument to the %s tag must be 'as'" % args[0])

    return FaqListNode(num=args[1], topic=args[2], varname=args[4])


@register.tag
def faq_list(parser, token):
    """
    returns a generic list of 'count' faq's to display in a list 
    ordered by the faq sort order.

    Example usage::
    
        {% faq_list 15 as faqs %}
    """
    args = token.split_contents()
    if len(args) != 4:
        raise template.TemplateSyntaxError("%s takes exactly three arguments" % args[0])
    if args[2] != 'as':
        raise template.TemplateSyntaxError("second argument to the %s tag must be 'as'" % args[0])

    return FaqListNode(num=args[1], varname=args[3])
