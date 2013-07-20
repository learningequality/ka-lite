from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('khanload.api_views',
    # Distributed server urls
    url(r'^oauth/$', 'update_all_callback', {}, 'update_all_callback'),
    url(r'^update/$', 'update_all', {}, 'update_all'),

    # Central server urls
    url(r'^user/exercises', 'user_exercises', {}, 'user_exercises'),
    url(r'^user/videos', 'user_videos', {}, 'user_videos'),
)