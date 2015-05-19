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
from fle_utils.internet.webcache import backend_cache_page
from kalite import topic_tools
from kalite.shared.decorators.auth import require_admin
from securesync.api_client import BaseClient
from securesync.models import Device, SyncSession, Zone


def check_setup_status(handler):
    """
    Decorator for validating that KA Lite post-install setup has completed.
    NOTE that this decorator must appear before the backend_cache_page decorator,
    so that it is run even when there is a cache hit.
    """
    def check_setup_status_wrapper_fn(request, *args, **kwargs):

        if "registered" not in request.session:
            logging.error("Key 'registered' not defined in session, but should be by now.")

        #Fix for #2047: prompt user to create an admin account if none exists
        if User.objects.exists():
            request.has_superuser = True
            # messages.warning(request, _("No administrator account detected. Please run 'kalite manage createsuperuser' from the terminal to create one."))

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
                    "Please login with the account you created while running the installation script, \
                    to complete the setup."))

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


@backend_cache_page
@render_to("knowledgemap/knowledgemap.html")
def exercise_dashboard(request):
    title = _("Your Knowledge Map")

    context = {
        "title": title,
        "data_url": settings.CONTENT_DATA_URL + settings.CHANNEL,
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
    query = request.GET.get('query')
    category = request.GET.get('category')
    max_results_per_category = request.GET.get('max_results', 25)

    # Outputs
    query_error = None
    possible_matches = {}
    hit_max = {}

    if query is None:
        query_error = _("Error: query not specified.")

#    elif len(query) < 3:
#        query_error = _("Error: query too short.")

    else:
        query = query.lower()
        # search for topic, video or exercise with matching title
        nodes = []
        for node_type, node_dict in topic_tools.get_node_cache().iteritems():
            if category and node_type != category:
                # Skip categories that don't match (if specified)
                continue

            possible_matches[node_type] = []  # make dict only for non-skipped categories
            for node in node_dict.values():
                title = _(node['title']).lower()  # this could be done once and stored.
                keywords = [x.lower() for x in node.get('keywords', [])]
                tags = [x.lower() for x in node.get('tags', [])]
                if title == query:
                    # Redirect to an exact match
                    return HttpResponseRedirect(reverse('learn') + node['path'])

                elif (len(possible_matches[node_type]) < max_results_per_category and
                    (query in title or query in keywords or query in tags)):
                    # For efficiency, don't do substring matches when we've got lots of results
                    possible_matches[node_type].append(node)


            hit_max[node_type] = len(possible_matches[node_type]) == max_results_per_category

    return {
        'title': _("Search results for '%(query)s'") % {"query": (query if query else "")},
        'query_error': query_error,
        'results': possible_matches,
        'hit_max': hit_max,
        'query': query,
        'max_results': max_results_per_category,
        'category': category,
    }

def create_superuser(request):
    if request.method == 'POST':
        if(request.POST.get('superusername', '') and request.POST.get('superpassword', '') 
            and request.POST.get('superemail', '') and '@' in request.POST['superemail']): 
            superusername = request.POST.get('superusername', '')
            superpassword = request.POST.get('superpassword', '')
            superemail = request.POST.get('superemail', '')
            if(len(superusername) < 30 and len(superpassword) < 30 and len(superemail) < 30):
                User.objects.create_superuser(username=superusername, password=superpassword, email=superemail)
                return HttpResponse(status=200)
            else:
                return HttpResponse(status=403)
        else:
            return HttpResponse(status=403)

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
        return HttpResponseRedirect(set_query_params(reverse("homepage"), {"next": request.get_full_path()}))

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
