from django.conf.urls import patterns, url, include
from django.conf import settings


urlpatterns = patterns(__package__ + '.views',
    url(r'^videos/$', 'update_videos', {}, 'update_videos'),
    url(r'^languages/$', 'update_languages', {}, 'update_languages')

)

#Else block url patterns can't be empty because we may have a reverse match for update_software.

if "Nalanda" in settings.CONFIG_PACKAGE:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^software/$', 'update_software', {}, 'update_software')

    )
else:
    urlpatterns += patterns(__package__ + '.views',
        url(r'^/$', 'update_software', {}, 'update_software')

    )
