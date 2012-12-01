import re, json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from annoying.decorators import render_to
from central.models import Organization, get_or_create_user_profile
from central.forms import OrganizationForm, ZoneForm
from securesync.api_client import SyncClient
from securesync.models import Zone, SyncSession
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from securesync.models import Facility
from securesync.forms import FacilityForm
import requests

import settings

@render_to("central/homepage.html")
def homepage(request):
    if not request.user.is_authenticated():
        return landing_page(request)
    organizations = get_or_create_user_profile(request.user).get_organizations()
    context = {'organizations': organizations}
    return context

@render_to("central/landing_page.html")
def landing_page(request):
    return {}
 
@login_required
@render_to("central/organization_form.html")
def organization_form(request, id=None):
    if id != "new":
        org = get_object_or_404(Organization, pk=id)
        if org.users.filter(pk=request.user.pk).count() == 0:
            return HttpResponseNotAllowed("You do not have permissions for this organization.")
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


@login_required
@render_to("central/zone_form.html")
def zone_form(request, id=None, org_id=None):
    org = get_object_or_404(Organization, pk=org_id)
    if org.users.filter(pk=request.user.pk).count() == 0:
        return HttpResponseNotAllowed("You do not have permissions for this organization.")
    if id != "new":
        zone = get_object_or_404(Zone, pk=id)
        if org.zones.filter(pk=zone.pk).count() == 0:
            return HttpResponseNotAllowed("This organization does not have permissions for this zone.")
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

@login_required
@render_to("securesync/facility_admin.html")
def central_facility_admin(request, zone_id=None):
    # still need to check if user has the rights to do this
    facilities = Facility.objects.all()
    context = {"facilities": facilities}
    return context

@login_required
@render_to("securesync/facility_edit.html")
def central_facility_edit(request, id=None, zone_id=None):
    if id != "new":
        facil = get_object_or_404(Facility, pk=id)
    else:
        facil = None
    if request.method == "POST":
        form = FacilityForm(data=request.POST, instance=facil)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("add_facility_student") + "?facility=" + form.instance.pk)
    else:
        form = FacilityForm(instance=facil)
    return {
        "form": form
    }

@render_to("central/getting_started.html")
def get_started(request):
    return {}

@login_required
def crypto_login(request):
    if not request.user.is_superuser:
        return HttpResponseNotAllowed()
    ip = request.GET.get("ip", "")
    if not ip:
        return HttpResponseNotFound("Please specify an IP (as a GET param).")
    host = "http://%s/" % ip
    client = SyncClient(host=host, require_trusted=False)
    if client.test_connection() != "success":
        return HttpResponse("Unable to connect to a KA Lite server at %s" % host)
    client.start_session() 
    if not client.session or not client.session.client_nonce:
        return HttpResponse("Unable to establish a session with KA Lite server at %s" % host)
    return HttpResponseRedirect("%ssecuresync/cryptologin/?client_nonce=%s" % (host, client.session.client_nonce))
    