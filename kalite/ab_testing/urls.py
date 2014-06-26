from django.conf.urls import patterns, url

# css and js templates
urlpatterns = patterns(__package__ + '.views',
    url(r'_generated/ab_testing.css', 'ab_testing_css', {}, 'ab_testing_css'),
    url(r'_generated/ab_testing.js', 'ab_testing_js', {}, 'ab_testing_js'),
)
