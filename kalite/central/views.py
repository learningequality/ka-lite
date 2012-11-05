import re, json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from annoying.decorators import render_to
from central.models import Organization
from central.forms import OrganizationForm, ZoneForm
from securesync.models import Zone
from django.core.urlresolvers import reverse

import settings

@render_to("central/homepage.html")
def homepage(request):
    organizations = request.user.get_profile().get_organizations()
    context = {'organizations': organizations}
    return context
      
@render_to("central/organization_form.html")
def organization_form(request, id=None):
    if id != "new":
        org = Organization.objects.get(pk=id)
    else:
        org = None
    if request.method == 'POST':
        form = OrganizationForm(data=request.POST, instance=org)
        if form.is_valid():
            # form.instance.owner = form.instance.owner or request.user 
            form.instance.save(owner=request.user)
            form.instance.users.add(request.user)
            # form.instance.save()
            return HttpResponseRedirect(reverse("homepage"))
    else:
        form = OrganizationForm(instance=org)
    return {
        'form': form
    } 

@render_to("central/zone_form.html")
def zone_form(request, id=None, org_id=None):
    org = get_object_or_404(Organization, pk=org_id)
    if id != "new":
        zone = Zone.objects.get(pk=id)
    else:
        zone = None
    if request.method == 'POST':
        form = ZoneForm(data=request.POST, instance=zone)
        if form.is_valid():
            # form.instance.owner = form.instance.owner or request.user 
            form.instance.save()
            org.zones.add(form.instance)
            # form.instance.save()
            return HttpResponseRedirect(reverse("homepage"))
    else:
        form = ZoneForm(instance=zone)
    return {
        'form': form
    } 