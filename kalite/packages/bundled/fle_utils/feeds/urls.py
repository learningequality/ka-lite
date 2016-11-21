from django.conf.urls import patterns, include, url

from . import RssSiteNewsFeed, AtomSiteNewsFeed


urlpatterns = patterns('',
    url(r'^addsubscription/$', 'add_subscription', {}, 'add_subscription'),
    url(r'^feeds/rss/$', RssSiteNewsFeed(), {}, 'rss_feed'),
    url(r'^feeds/atom/$', AtomSiteNewsFeed(), {}, 'atom_feed'),
)
