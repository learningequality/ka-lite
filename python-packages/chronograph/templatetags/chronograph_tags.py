from django import template
from django.core.urlresolvers import reverse, NoReverseMatch

register = template.Library()

class RunJobURLNode(template.Node):
    def __init__(self, object_id):
        self.object_id = template.Variable(object_id)
        
    def render(self, context):
        object_id = self.object_id.resolve(context)
        try:
            # Old way
            url = reverse('chronograph_job_run', args=(object_id,))
        except NoReverseMatch:
            # New way
            url = reverse('admin:chronograph_job_run', args=(object_id,))
        return url

def do_get_run_job_url(parser, token):
    """
    Returns the URL to the view that does the 'run_job' command.
    
    Usage::
    
        {% get_run_job_url [object_id] %}
    """
    try:
        # Splitting by None == splitting by spaces.
        tag_name, object_id = token.contents.split(None, 1)
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires one argument" % token.contents.split()[0]
    return RunJobURLNode(object_id)

register.tag('get_run_job_url', do_get_run_job_url)