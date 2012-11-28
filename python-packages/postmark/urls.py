from django.conf.urls.defaults import *

urlpatterns = patterns("",
    url(r"^bounce/$", "postmark.views.bounce", name="postmark_bounce_hook"),
)