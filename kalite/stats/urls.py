from django.conf.urls.defaults import patterns, include, url

urlpatterns = patterns('stats.views',
    # HACK(bcipolli) Admin summary page (no org info needed)
    url(r'^summary/$', 'admin_summary_page', {}, 'admin_summary_page'),
)

