from annoying.decorators import render_to
from . import loader

@render_to("handlebars/template_js.html")
def render_template_js(request, module_name):
    return {"templates": loader.load_template_sources(module_name)}
