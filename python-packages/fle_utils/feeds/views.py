from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from .models import Subscription
from fle_utils.django_utils.functions import get_request_ip


@csrf_exempt # because we want the front page to cache properly
def add_subscription(request):
    if request.method == "POST":
        sub = Subscription(email=request.POST.get("email"))
        sub.ip = get_request_ip(request) or ""
        sub.save()
        messages.success(request, _("A subscription for '%s' was added.") % request.POST.get("email"))
    return HttpResponseRedirect(reverse("homepage"))
