"""
Views for the KA Lite app are wide-ranging, and include:
* Serving the homepage, videos, exercise pages.
* Dealing with caching
* Administrative pages
and more!
"""
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from itertools import islice

from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, HttpResponse
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from fle_utils.internet.classes import JsonResponseMessageError
from fle_utils.internet.functions import get_ip_addresses, set_query_params
from kalite import topic_tools
from kalite.shared.decorators.auth import require_admin
from securesync.api_client import BaseClient
from securesync.models import Device, SyncSession, Zone
from kalite.distributed.forms import SuperuserForm
import json


def check_setup_status(handler):
    """
    Decorator for validating that KA Lite post-install setup has completed.
    NOTE that this decorator must appear before the backend_cache_page decorator,
    so that it is run even when there is a cache hit.
    """
    def check_setup_status_wrapper_fn(request, *args, **kwargs):

        if "registered" not in request.session:
            logging.error("Key 'registered' not defined in session, but should be by now.")

        if User.objects.exists():
            request.has_superuser = True
            # next line is for testing
            # User.objects.all().delete()

        if request.is_admin:
            # TODO(bcipolli): move this to the client side?
            if not request.session.get("registered", True) and BaseClient().test_connection() == "success":
                # Being able to register is more rare, so prioritize.
                messages.warning(request, mark_safe("Please <a href='%s'>follow the directions to register your device</a>, so that it can synchronize with the central server." % reverse("register_public_key")))
            elif not request.session["facility_exists"]:
                zone_id = (Zone.objects.all() and Zone.objects.all()[0].id) or "None"
                messages.warning(request, mark_safe("Please <a href='%s'>create a facility</a> now. Users will not be able to sign up for accounts until you have made a facility." % reverse("add_facility", kwargs={"zone_id": zone_id})))

        elif not request.is_logged_in:
            if not request.session.get("registered", True) and BaseClient().test_connection() == "success":
                # Being able to register is more rare, so prioritize.
                redirect_url = reverse("register_public_key")
            elif not request.session["facility_exists"]:
                zone = Device.get_own_device().get_zone()
                zone_id = "None" if not zone else zone.id
                redirect_url = reverse("add_facility", kwargs={"zone_id": zone_id})
            else:
                redirect_url = None
            if redirect_url:
                messages.warning(request, mark_safe(
                    "Please login with the admin account you created, then create your facility and register this device to complete the setup."))

        return handler(request, *args, **kwargs)
    return check_setup_status_wrapper_fn


@render_to("distributed/learn.html")
def learn(request):
    """
    Render the all-in-one sidebar navigation/content-viewing app.
    """
    context = {
        "load_perseus_assets": settings.LOAD_KHAN_RESOURCES,
        "channel": settings.CHANNEL,
        "pdfjs": settings.PDFJS,
    }
    return context


@check_setup_status
@render_to("distributed/homepage.html")
def homepage(request):
    """
    Homepage.
    """
    return {}

def watch_home(request):
    """Dummy wrapper function for topic_handler with url=/"""
    return topic_handler(request, cached_nodes={"topic": topic_tools.get_topic_tree()})


def help(request):
    if request.is_admin:
        return help_admin(request)
    else:
        return help_student(request)


@require_admin
@render_to("distributed/help_admin.html")
def help_admin(request):
    context = {
        "wiki_url" : settings.CENTRAL_WIKI_URL,
        "ips": get_ip_addresses(include_loopback=False),
        "port": request.META.get("SERVER_PORT") or settings.USER_FACING_PORT(),
    }
    return context


@render_to("distributed/help_student.html")
def help_student(request):

    context = {
        "wiki_url" : settings.CENTRAL_WIKI_URL,
    }
    return context


@require_admin
def zone_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()
    return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": (zone and zone.pk) or "None"}))


@require_admin
def device_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()

    return HttpResponseRedirect(reverse("device_management", kwargs={"zone_id": (zone and zone.pk) or None, "device_id": device.pk}))


@render_to('distributed/search_page.html')
def search(request):
    # Inputs
    page = int(request.GET.get('page', 1))
    query = request.GET.get('query')
    category = request.GET.get('category')
    max_results_per_category = request.GET.get('max_results', 25)

    # Outputs
    query_error = None
    possible_matches = {}
    hit_max = {}


    node_kinds = {
        "Topic": ["Topic"],
        "Exercise": ["Exercise"],
        "Content": ["Video", "Audio", "Document"],
    }

    if query is None:
        query_error = _("Error: query not specified.")

#    elif len(query) < 3:
#        query_error = _("Error: query too short.")

    else:
        query = query.lower()
        # search for topic, video or exercise with matching title
        for node_type, node_dict in topic_tools.get_node_cache().iteritems():
            if category and node_type != category:
                # Skip categories that don't match (if specified)
                continue

            exact_match = filter(lambda node: node["kind"] in node_kinds[node_type] and node["title"].lower() == query, node_dict.values())[:1]

            if exact_match:
                # Redirect to an exact match
                return HttpResponseRedirect(reverse('learn') + exact_match[0]['path'])

            # For efficiency, don't do substring matches when we've got lots of results
            match_generator = (node for node in node_dict.values()
                if node["kind"] in node_kinds[node_type] and (query in node["title"].lower() or query in [x.lower() for x in node.get('keywords', [])] or
                query in [x.lower() for x in node.get('tags', [])]))

            # Only return max results
            try:
                possible_matches[node_type] = list(islice(match_generator, (page-1)*max_results_per_category, page*max_results_per_category))
            except ValueError:
                return HttpResponseNotFound("Page does not exist")

            hit_max[node_type] = next(match_generator, False)

    previous_params = request.GET.copy()
    previous_params['page'] = page - 1

    previous_url = "?" + previous_params.urlencode()

    next_params = request.GET.copy()
    next_params['page'] = page + 1

    next_url = "?" + next_params.urlencode()

    return {
        'title': _("Search results for '%(query)s'") % {"query": (query if query else "")},
        'query_error': query_error,
        'results': possible_matches,
        'hit_max': hit_max,
        'more': any(hit_max.values()),
        'page': page,
        'previous_url': previous_url,
        'next_url': next_url,
        'query': query,
        'max_results': max_results_per_category,
        'category': category,
    }

def add_superuser_form(request):
    if request.method == 'GET':
        form = SuperuserForm()
        return_html = render_to_string('admin/superuser_form.html', {'form': form}, context_instance=RequestContext(request))
        data = {'Status' : 'ShowModal', 'data' : return_html}
        return HttpResponse(json.dumps(data), content_type="application/json")

def create_superuser(request):
    if request.method == 'POST':
        form = SuperuserForm(request.POST)
        if form.is_valid():
            # security precaution
            cd = form.cleaned_data
            superusername = cd.get('superusername')
            superpassword = cd.get('superpassword')
            confirmsuperpassword = cd.get('confirmsuperpassword')
            if superpassword != confirmsuperpassword:
                form.errors['confirmsuperpassword'] = form.error_class([_("Passwords don't match!")])
                return_html = render_to_string('admin/superuser_form.html', {'form': form}, context_instance=RequestContext(request))
                data = {'Status' : 'Invalid', 'data' : return_html}
            else:
                superemail = "superuser@learningequality.org"
                User.objects.create_superuser(username=superusername, password=superpassword, email=superemail)
                data = {'Status' : 'Success'}
        else:
            cd = form.cleaned_data
            if cd.get('confirmsuperpassword') != cd.get('superpassword'):
                form.errors['confirmsuperpassword'] = form.error_class([_("Passwords don't match!")])
            return_html = render_to_string('admin/superuser_form.html', {'form': form}, context_instance=RequestContext(request))
            data = {'Status' : 'Invalid', 'data' : return_html}

        return HttpResponse(json.dumps(data), content_type="application/json")

def crypto_login(request):
    """
    Remote admin endpoint, for login to a distributed server (given its IP address; see central/views.py:crypto_login)

    An admin login is negotiated using the nonce system inside SyncSession
    """
    if "client_nonce" in request.GET:
        client_nonce = request.GET["client_nonce"]
        try:
            session = SyncSession.objects.get(client_nonce=client_nonce)
        except SyncSession.DoesNotExist:
            return HttpResponseServerError("Session not found.")
        if session.server_device.is_trusted():
            user = get_object_or_None(User, username="centraladmin")
            if not user:
                user = User(username="centraladmin", is_superuser=True, is_staff=True, is_active=True)
                user.set_unusable_password()
                user.save()
            user.backend = "django.contrib.auth.backends.ModelBackend"
            auth_login(request, user)
        session.delete()
    return HttpResponseRedirect(reverse("homepage"))


def handler_403(request, *args, **kwargs):
    context = RequestContext(request)
    #message = None  # Need to retrieve, but can't figure it out yet.

    if request.is_ajax():
        return JsonResponseMessageError(_("You must be logged in with an account authorized to view this page (API)."), status=403)
    else:
        messages.error(request, mark_safe(_("You must be logged in with an account authorized to view this page.")))
        return HttpResponseRedirect(set_query_params(reverse("homepage"), {"next": request.get_full_path(), "login": True}))

@render_to("distributed/perseus.html")
def perseus(request):
    return {}

def handler_404(request):
    return HttpResponseNotFound(render_to_string("distributed/404.html", {}, context_instance=RequestContext(request)))


def handler_500(request):
    errortype, value, tb = sys.exc_info()
    context = {
        "errortype": errortype.__name__,
        "value": unicode(value),
    }
    return HttpResponseServerError(render_to_string("distributed/500.html", context, context_instance=RequestContext(request)))
