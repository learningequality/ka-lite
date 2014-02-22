import re
import json
import tempfile
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt

import kalite
import settings
from central.forms import OrganizationForm, OrganizationInvitationForm
from central.models import Organization, OrganizationInvitation, DeletionRecord, get_or_create_user_profile, FeedListing, Subscription
from securesync.engine.api_client import SyncClient
from securesync.models import Zone
from shared.decorators import require_authorized_admin
from utils.django_utils import get_request_ip


def get_central_server_host(request):
    """
    Nice to refer to the central server in a simple way.
    Note that CENTRAL_SERVER_HOST usually isn't set for the central server,
    so it's kind of a bogus fallback.
    """
    return request.get_host() or getattr(settings, CENTRAL_SERVER_HOST, "")


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
def org_management(request, org_id=None):
    """Management of all organizations for the given user"""

    # get a list of all the organizations this user helps administer
    organizations = get_or_create_user_profile(request.user).get_organizations()

    # add invitation forms to each of the organizations
    for org in organizations.values():
        org.form = OrganizationInvitationForm(initial={"invited_by": request.user})

    # handle a submitted invitation form
    if request.method == "POST":
        form = OrganizationInvitationForm(data=request.POST)
        if form.is_valid():
            # ensure that the current user is a member of the organization to which someone is being invited
            if not form.instance.organization.is_member(request.user):
                raise PermissionDenied(_("Unfortunately for you, you do not have permission to do that."))
            # send the invitation email, and save the invitation record
            form.instance.send(request)
            form.save()
            return HttpResponseRedirect(reverse("org_management"))
        else: # we need to inject the form into the correct organization, so errors are displayed inline
            for pk,org in organizations.items():
                if org.pk == int(request.POST.get("organization")):
                    org.form = form

    zones = {}
    for org in organizations.values():
        zones[org.pk] = []
        for zone in list(org.get_zones()):
            zones[org.pk].append({
                "id": zone.id,
                "name": zone.name,
                "is_deletable": not zone.has_dependencies(passable_classes=["Organization"]),
            })
    return {
        "title": _("Account administration"),
        "organizations": organizations,
        "zones": zones,
        "HEADLESS_ORG_NAME": Organization.HEADLESS_ORG_NAME,
        "my_invitations": list(OrganizationInvitation.objects \
            .filter(email_to_invite=request.user.email)
            .order_by("organization__name")),
        "download_url": reverse("install"),
    }


@csrf_exempt # because we want the front page to cache properly
def add_subscription(request):
    if request.method == "POST":
        sub = Subscription(email=request.POST.get("email"))
        sub.ip = get_request_ip(request) or ""
        sub.save()
        messages.success(request, _("A subscription for '%s' was added.") % request.POST.get("email"))
    return HttpResponseRedirect(reverse("homepage"))


@login_required
def org_invite_action(request, invite_id):
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    org = invite.organization
    if request.user.email != invite.email_to_invite:
        raise PermissionDenied(_("It's not nice to force your way into groups."))
    if request.method == "POST":
        data = request.POST
        if data.get("join"):
            messages.success(request, _("You have joined ") + org.name + _(" as an admin."))
            org.add_member(request.user)
        if data.get("decline"):
            messages.warning(request, _("You have declined to join ") + org.name + _(" as an admin."))
        invite.delete()
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
def delete_admin(request, org_id, user_id):
    org = Organization.objects.get(pk=org_id)
    admin = org.users.get(pk=user_id)
    if org.owner == admin:
        raise PermissionDenied(_("The owner of an organization cannot be removed."))
    if request.user == admin:
        raise PermissionDenied(_("Your personal views are your own, but in this case ") +
            _("you are not allowed to delete yourself."))
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_user=admin)
    deletion.save()
    org.users.remove(admin)
    messages.success(request, _("You have successfully removed ") + admin.username + _(" as an administrator for ") + org.name + ".")
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
def delete_invite(request, org_id, invite_id):
    org = Organization.objects.get(pk=org_id)
    invite = OrganizationInvitation.objects.get(pk=invite_id)
    deletion = DeletionRecord(organization=org, deleter=request.user, deleted_invite=invite)
    deletion.save()
    invite.delete()
    messages.success(request, _("You have successfully revoked the invitation for ") + invite.email_to_invite + ".")
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
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

@require_authorized_admin
def delete_organization(request, org_id):
    org = Organization.objects.get(pk=org_id)
    num_zones = org.get_zones().count()
    if num_zones > 0:
        messages.error(request, _("You cannot delete '%(name)s' because it has %(num_zones)s sharing network(s) affiliated with it.") % {
            "name": org.name,
            "num_zones": num_zones,
        })
    else:
        messages.success(request, _("You have successfully deleted %(org_name)s.") % {"org_name": org.name})
        org.delete()
    return HttpResponseRedirect(reverse("org_management"))


@require_authorized_admin
def delete_zone(request, org_id, zone_id):
    zone = get_object_or_404(Zone, id=zone_id)
    if not zone.has_dependencies(passable_classes=["Organization"]):
        zone.delete()
        messages.success(request, _("You have successfully deleted ") + zone.name + ".")
    else:
        messages.warning(request, _("You cannot delete this zone because it is syncing data with with %d device(s)") % zone.devicezone_set.count())
    return HttpResponseRedirect(reverse("org_management"))


def content_page(request, page, **kwargs):
    context = RequestContext(request)
    context.update(kwargs)
    return render_to_response("central/content/%s.html" % page, context_instance=context)


@render_to("central/glossary.html")
def glossary(request):
    return {}


def get_request_var(request, var_name, default_val="__empty__"):
    """
    Allow getting parameters from the POST object (from submitting a HTML form),
    or on the querystring.

    This isn't very RESTful, but it makes a lot of sense to me!
    """
    return  request.POST.get(var_name, request.GET.get(var_name, default_val))


def download_wizard(request, edition=None):
    """
    NOTE that this wizard is ONLY PARTIALLY FUNCTIONAL (see below)

    Install wizard accepts "edition" as an optional argument.

    If the user is not logged in, they are shown both choices.
    If they select edition=single-server, then they download right away.

    If the user is logged in, they are only shown the multiple-servers edition.
    When they submit the form (to choose the zone), they get the download package.

    TODO(bcipolli):
    * Don't show org, only show zone.
    * If a user has more than one organization, you only get zone information for the first zone.
    there's no way to show information from other orgs.
        If the user is logged in, theyIf not sent, the user has two options: "single server" or "multiple server".

    """
    if not edition and request.user.is_anonymous():
        @render_to("central/download_wizard.html")
        def wizard_fn(request):
            return {}
        return wizard_fn(request)

    elif edition == "multiple-server" or not request.user.is_anonymous():
        return download_multiple_server_edition(request)

    elif edition == "single-server":
        return download_single_server_edition(request)

    else:
        raise Http404("Unknown server edition: %s" % edition)



@render_to("central/download_thankyou.html")
def download_thankyou(request, **kwargs):
    return kwargs


def download_single_server_edition(request):
    """
    """
    version = get_request_var(request, "version",  kalite.VERSION)
    platform = get_request_var(request, "platform", "all")
    locale = get_request_var(request, "locale", "en")

    return download_thankyou(
        request,
        version=kalite.VERSION,
        download_url=reverse("download_kalite_public", kwargs={
            "version": kalite.VERSION,
            "platform": platform,
            "locale": locale,
        }),
    )


@login_required
def download_multiple_server_edition(request):
    # get a list of all the organizations this user helps administer,
    #   then choose the selected organization (if possible)
    # Get all data
    zone_id = get_request_var(request, "zone", None)
    kwargs={
        "version": kalite.VERSION,
        "platform": get_request_var(request, "platform", "all"),
        "locale": get_request_var(request, "locale", "en"),
        "include_data": bool(get_request_var(request, "include_data", True)),
    }

    # Loop over orgs and zones, building the dict of all zones
    #   while searching for the zone_id.

    zones = []
    for org in request.user.organization_set.all().order_by("name"):
        for zone in org.zones.all().order_by("name"):
            if zone_id and zone_id == zone.id:
                kwargs["zone_id"] = zone_id
                return download_thankyou(
                    request,
                    version=kwargs["version"],
                    download_url=reverse("download_kalite_private", kwargs=kwargs),
                )
            else:
                zones.append({
                    "id": zone.id,
                    "name": "%s / %s" % (org.name, zone.name),
                })

    # If we get here, then we failed to find the zone.
    if zone_id:
        if Zone.objects.filter(id=zone_id):
            # The zone exists, we must just not have access to it
            raise PermissionDenied()
        else:
            # We didnt't find it because it doesn't exist
            raise Http404(_("Zone ID not found: %s") % zone_id)

    # If we get here, then no zone was specified.  So list the options.
    if len(zones) == 1:
        zone_id = zones[0]["id"]

    @render_to("central/download_wizard.html")
    def wizard_fn(request):
        return {
            "zones": zones,
            "selected_zone": zone_id or (zones[0]["id"] if len(zones) == 1 else None),
            "edition": "multiple-server",
        }
    return wizard_fn(request)


def download_kalite_public(request, *args, **kwargs):
    """
    Download the public version of KA Lite--make sure they don't
    try to sneak in unauthorized zone info!
    """
    if "zone_id" in kwargs or "zone" in request.REQUEST:
        raise PermissionDenied(_("Must be logged in to download with zone information."))
    return download_kalite(request, *args, **kwargs)


@login_required
def download_kalite_private(request, *args, **kwargs):
    """
    Download with zone info--will authenticate that zone info
    below.
    """
    zone_id = kwargs.get("zone_id") or request.REQUEST.get("zone")
    if not zone_id:
        # No zone information = bad request (400)
        return HttpResponse(_("Must specify zone information."), status=400)

    kwargs["zone_id"] = zone_id
    return download_kalite(request, *args, **kwargs)


def download_kalite(request, *args, **kwargs):
    """
    A request to download KA Lite, either without zone info, or with it.
    If with it, then we have to make sure it's OK for this user.

    This endpoint is also set up to deal with platform, locale, and version,
    though right now only direct URLs would set this (not via the download wizard).
    """

    # Parse args
    zone = get_object_or_None(Zone, id=kwargs.get('zone_id', None))
    platform = kwargs.get("platform", "all")
    locale = kwargs.get("locale", "en")
    version = kwargs.get("version", kalite.VERSION)
    if version == "latest":
        version = kalite.VERSION

    # Make sure this user has permission to admin this zone
    if zone and not request.user.is_authenticated():
        raise PermissionDenied(_("Requires authentication"))
    elif zone:
        zone_orgs = Organization.from_zone(zone)
        if not zone_orgs or not set([org.id for org in zone_orgs]).intersection(set(get_or_create_user_profile(request.user).get_organizations().keys())):
            raise PermissionDenied(_("You are not authorized to access this zone information."))

    # Generate the zip file.  Pre-specify the zip filename,
    #   as we won't know the output location otherwise.
    zip_file = tempfile.mkstemp()[1]
    call_command(
        "package_for_download",
        file=zip_file,
        central_server=get_central_server_host(request),
        **kwargs
    )

    # Build the outgoing filename."
    user_facing_filename = "kalite"
    for val in [platform, locale, kalite.VERSION, zone.name if zone else None]:
        user_facing_filename +=  ("-%s" % val) if val not in [None, "", "all"] else ""
    user_facing_filename += ".zip"

    # Stream it back to the user
    zh = open(zip_file,"rb")
    response = HttpResponse(content=zh, mimetype='application/zip', content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="%s"' % user_facing_filename

    # Not sure if we could remove the zip file here; possibly not,
    #   if it's a streaming response or byte-range reesponse
    return response


@login_required
def crypto_login(request):
    """
    Remote admin endpoint, for login to a distributed server (given its IP address; see also securesync/views.py:crypto_login)

    An admin login is negotiated using the nonce system inside SyncSession
    """
    if not request.user.is_superuser:
        raise PermissionDenied()
    ip = request.GET.get("ip", "")
    if not ip:
        return HttpResponseNotFound(_("Please specify an IP (as a GET param)."))
    host = "http://%s/" % ip
    client = SyncClient(host=host, require_trusted=False)
    if client.test_connection() != "success":
        return HttpResponse(_("Unable to connect to a KA Lite server at %s") % host)
    client.start_session()
    if not client.session or not client.session.client_nonce:
        return HttpResponse(_("Unable to establish a session with KA Lite server at %s") % host)
    return HttpResponseRedirect("%ssecuresync/cryptologin/?client_nonce=%s" % (host, client.session.client_nonce))


def handler_403(request, *args, **kwargs):
    context = RequestContext(request)
    message = None  # Need to retrieve, but can't figure it out yet.

    if request.is_ajax():
        raise PermissionDenied(message)
    else:
        messages.error(request, mark_safe(_("You must be logged in with an account authorized to view this page.")))
        return HttpResponseRedirect(reverse("auth_login") + "?next=" + request.path)

def handler_404(request):
    return HttpResponseNotFound(render_to_string("central/404.html", {}, context_instance=RequestContext(request)))

def handler_500(request):
    return HttpResponseServerError(render_to_string("central/500.html", {}, context_instance=RequestContext(request)))
