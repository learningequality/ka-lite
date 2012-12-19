from __future__ import absolute_import

from django.conf.urls.defaults import *
from . import views as faq_views

urlpatterns = patterns('',
    url(regex = r'^$',
        view  = faq_views.TopicList.as_view(),
        name  = 'faq_topic_list',
    ),
    url(regex = r'^submit/$',
        view  = faq_views.SubmitFAQ.as_view(),
        name  = 'faq_submit',
    ),
    url(regex = r'^submit/thanks/$',
        view  = faq_views.SubmitFAQThanks.as_view(),
        name  = 'faq_submit_thanks',
    ),
    url(regex = r'^(?P<slug>[\w-]+)/$',
        view  = faq_views.TopicDetail.as_view(),
        name  = 'faq_topic_detail',
    ),
    url(regex = r'^(?P<topic_slug>[\w-]+)/(?P<slug>[\w-]+)/$',
        view  = faq_views.QuestionDetail.as_view(),
        name  = 'faq_question_detail',
    ),
)