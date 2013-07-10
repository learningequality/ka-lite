import re
import json
from annoying.decorators import render_to

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, HttpResponseNotAllowed, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

import kalite
import settings
from central.forms import OrganizationForm, OrganizationInvitationForm
from central.models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile, FeedListing, Subscription
from securesync.api_client import SyncClient
from utils.decorators import authorized_login_required


@render_to("central/homepage.html")
def homepage(request):
    feed = FeedListing.objects.order_by('-posted_date')[:5]
    return {
        "feed": feed,
        "central_contact_email": settings.CENTRAL_CONTACT_EMAIL,
        "wiki_url": settings.CENTRAL_WIKI_URL
    }

@login_required
@render_to("central/org_management.html")
def org_management(request):
    """Management of all organizations for the given user"""

    # get a list of all the organizations this user helps administer
    organizations = get_or_create_user_profile(request.user).get_organizations()

    # add invitation forms to each of the organizations
    for pk,org in organizations.items():
        org.form = OrganizationInvitationForm(initial={"invited_by": request.user})

    # handle a submitted invitation form
    if request.method == "POST":
        form = OrganizationInvitationForm(data=request.POST)
        if form.is_valid():
            # ensure that the current user is a member of the organization to which someone is being invited
            if not form.instance.organization.is_member(request.user):
                return HttpResponseForbidden("Unfortunately for you, you do not have permission to do that.")
            # send the invitation email, and save the invitation record
            form.instance.send(request)
            form.save()
            return HttpResponseRedirect(reverse("org_management"))
        else: # we need to inject the form into the correct organization, so errors are displayed inline
            for pk,org in organizations.items():
                if org.pk == int(request.POST.get("organization")):
                    org.form = form

    return {
        "title": _("Account administration"),
        "organizations": organizations,
        "invitations": OrganizationInvitation.objects.filter(email_to_invite=request.user.email)
    }


@csrf_exempt # because we want the front page to cache properly
def add_subscription(request):
    if request.method == "POST":
        sub = Subscription(email=request.POST.get("email"))
        sub.ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get('REMOTE_ADDR', ""))
        sub.save()
        messages.success(request, "A subscription for '%s' was added." % request.POST.get("email"))
    return HttpResponseRedirect(reverse("homepage"))

@login_required
def org_invite_action(request, invite_id):
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    org = invite.organization
    if request.user.email != invite.email_to_invite:
        return HttpResponseForbidden("It's not nice to force your way into groups.")
    if request.method == "POST":
        data = request.POST
        if data.get("join"):
            messages.success(request, "You have joined " + org.name + " as an admin.")
            org.add_member(request.user)
        if data.get("decline"):
            messages.warning(request, "You have declined to join " + org.name + " as an admin.")
        invite.delete()
    return HttpResponseRedirect(reverse("org_management"))


@authorized_login_required
def delete_admin(request, org_id, user_id):
    org = Organization.objects.get(pk=org_id)
    admin = org.users.get(pk=user_id)
    if org.owner == admin:
        return HttpResponseForbidden("The owner of an organization cannot be removed.")
    if request.user == admin:
        return HttpResponseForbidden("Your personal views are your own, but in this case " +
            "you are not allowed to delete yourself.")
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_user=admin)
    deletion.save()
    org.users.remove(admin)
    messages.success(request, "You have succesfully removed " + admin.username + " as an administrator for " + org.name + ".")
    return HttpResponseRedirect(reverse("org_management"))


@authorized_login_required
def delete_invite(request, org_id, invite_id):
    org = Organization.objects.get(pk=org_id)
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_invite=invite)
    deletion.save()
    invite.delete()
    messages.success(request, "You have succesfully revoked the invitation for " + invite.email_to_invite + ".")
    return HttpResponseRedirect(reverse("org_management"))


@authorized_login_required
@render_to("central/organization_form.html")
def organization_form(request, org_id):
    if org_id != "new":
        org = get_object_or_404(Organization, pk=org_id)
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
                return HttpResponseRedirect(reverse("org_management"))
            else:
                return HttpResponseRedirect(reverse("zone_form", kwargs={"zone_id": "new", "org_id": form.instance.pk}) )
    else:
        form = OrganizationForm(instance=org)
    return {
        'form': form
    }


@render_to("central/glossary.html")
def glossary(request):
    return {}


@login_required
def crypto_login(request):
    if not request.user.is_superuser:
        return HttpResponseForbidden()
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



def handler_404(request):
    return HttpResponseNotFound(render_to_string("central/404.html", {}, context_instance=RequestContext(request)))

def handler_500(request):
    return HttpResponseServerError(render_to_string("central/500.html", {}, context_instance=RequestContext(request)))
