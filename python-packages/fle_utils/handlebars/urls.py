from django.conf.urls.defaults import patterns, url, include

urlpatterns = patterns(__package__ + '.views',
    url(r'^templates/(?P<module_name>\w+).js$', 'render_template_js', {}, 'handlebars_templates'),
)

