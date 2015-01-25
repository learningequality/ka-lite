from django.conf.urls import patterns, url

# css and js templates
urlpatterns = patterns(__package__ + '.views',
    url(r'dynamic.js$', 'dynamic_js', {}, 'dynamic_js'),
    url(r'dynamic.css$', 'dynamic_css', {}, 'dynamic_css'),
)
