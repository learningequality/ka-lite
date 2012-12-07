import re, json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseNotAllowed
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from annoying.decorators import render_to
from central.models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile
from central.forms import OrganizationForm, ZoneForm, OrganizationInvitationForm
from securesync.api_client import SyncClient
from securesync.models import Zone, SyncSession
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from securesync.models import Facility
from securesync.forms import FacilityForm
from django.contrib import messages
import requests

import settings

@render_to("central/homepage.html")
def homepage(request):
    if not request.user.is_authenticated():
        return landing_page(request)
    organizations = get_or_create_user_profile(request.user).get_organizations()
    for org in organizations:
        org.form = OrganizationInvitationForm(initial={"invited_by": request.user})
    if request.method == 'POST':
        form = OrganizationInvitationForm(data=request.POST)
        for org in organizations:
            if org.pk == int(request.POST.get('organization')):
                org.form = form
        if form.is_valid():
            if not form.instance.organization.is_member(request.user):
                return HttpResponseNotAllowed("Unfortunately for you, you do not have permission to do that.")
            form.instance.send(request)
            form.save()
            return HttpResponseRedirect(reverse("homepage"))
    user = request.user
    received_invitations = OrganizationInvitation.objects.filter(email_to_invite=user.email)
    context = {
        'user': user,
        'organizations': organizations,
        'sent_invitations': OrganizationInvitation.objects.filter(invited_by=user),
        'received_invitations': received_invitations
    }
    return context

def org_invite_action(request, invite_id):
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    org = Organization.objects.get(pk=invite.organization.pk)
    if request.user.email != invite.email_to_invite:
        return HttpResponseNotAllowed("It's not nice to force your way into groups.")
    if request.method == 'POST':
        data = request.POST
        if data.get('join'):
            messages.success(request, "You have joined " + org.name + " as an admin.")
            org.add_member(request.user)
        if data.get('decline'):
            messages.warning(request, "You have declined to join " + org.name + " as an admin.")
        invite.delete()
    return HttpResponseRedirect(reverse("homepage"))

def delete_admin(request, org_id, user_id):
    org = Organization.objects.get(pk=org_id)
    admin = org.users.get(pk=user_id)
    if org.owner == admin:
        return HttpResponseNotAllowed("This admin is the owner of this organization. Please contact us if you are sure you need to remove this user.")
    if request.user == admin:
        return HttpResponseNotAllowed("Your personal views are your own, but here at KA-Lite, you are not allowed to delete yourself.")
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_user=admin)
    deletion.save()
    org.users.remove(admin)
    messages.success(request, "You have succesfully removed " + admin.username + " as an administrator for " + org.name + ".")
    return HttpResponseRedirect(reverse("homepage"))

def delete_invite(request, org_id, invite_id):
    org = Organization.objects.get(pk=org_id)
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_invite=invite)
    deletion.save()
    invite.delete()
    messages.success(request, "You have succesfully revoked the invitation for " + invite.email_to_invite + ".")
    return HttpResponseRedirect(reverse("homepage"))

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
            old_org = bool(form.instance.pk)
            form.instance.save(owner=request.user)
            form.instance.users.add(request.user)
            # form.instance.save()
            if old_org:
                return HttpResponseRedirect(reverse("homepage"))
            else:    
                return HttpResponseRedirect(reverse("zone_form", kwargs={"id": "new", "org_id": form.instance.pk}) )
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
    return {
        "zone_id": zone_id,
        "facilities": facilities,
    } 

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
            form.instance.zone_fallback = get_object_or_404(Zone, pk=zone_id)
            form.save()
            return HttpResponseRedirect(reverse("central_facility_admin", kwargs={"zone_id": zone_id}))
    else:
        form = FacilityForm(instance=facil)
    return {
        "form": form,
        "zone_id": zone_id,
    }

@render_to("central/getting_started.html")
def get_started(request):
    return {}

@render_to("central/glossary.html")
def glossary(request):
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
    