"""
"""
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from kalite.shared.decorators import require_login

@require_login
@render_to("store/store.html")
def store(request):
    return {}
