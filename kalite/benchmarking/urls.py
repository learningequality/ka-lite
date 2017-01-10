from django.conf.urls import patterns, url


urlpatterns = patterns(__package__ + '.views',
                       url(r'^benchmarking', 'benchmarking',
                           {}, name='benchmarking'),
                       )
