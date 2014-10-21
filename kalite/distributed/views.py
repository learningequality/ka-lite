"""
Views for the KA Lite app are wide-ranging, and include:
* Serving the homepage, videos, exercise pages.
* Dealing with caching
* Administrative pages
and more!
"""
import copy
import json
import os
import re
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
from functools import partial

from django.contrib.auth import login as auth_login
from django.contrib.auth.models import User
from django.conf import settings; logging = settings.LOG
from django.contrib import messages
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.i18n import javascript_catalog

from fle_utils.django_utils import is_loopback_connection
from fle_utils.internet import JsonResponse, JsonResponseMessageError, get_ip_addresses, set_query_params, backend_cache_page
from kalite import topic_tools
from kalite.facility.models import Facility, FacilityUser,FacilityGroup
from kalite.i18n import select_best_available_language
from kalite.main.models import VideoLog, ExerciseLog
from kalite.playlist.views import view_playlist
from kalite.shared.decorators import require_admin
from kalite.updates import stamp_availability_on_topic, stamp_availability_on_video, do_video_counts_need_update_question_mark
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
                    "Please <a href='%s?next=%s'>login</a> with the account you created while running the installation script, \
                    to complete the setup." % (reverse("login"), redirect_url)))

        return handler(request, *args, **kwargs)
    return check_setup_status_wrapper_fn


def refresh_topic_cache(handler, force=False):

    def strip_counts_from_ancestors(node):
        """
        Remove relevant counts from all ancestors
        """
        for ancestor_id in node.get("ancestor_ids", []):
            ancestor = topic_tools.get_ancestor(node, ancestor_id)
            if "nvideos_local" in ancestor:
                del ancestor["nvideos_local"]
            if "nvideos_known" in ancestor:
                del ancestor["nvideos_known"]
        return node

    def recount_videos_and_invalidate_parents(node, force=False, stamp_urls=False):
        """
        Call stamp_video_availability (if necessary); if a change has been detected,
        then check parents to see if their counts should be invalidated.
        """
        do_it = force
        do_it = do_it or "nvideos_local" not in node
        do_it = do_it or any(["nvideos_local" not in child for child in node.get("children", [])])
        if do_it:
            logging.debug("Adding video counts %s%sto topic (and all descendants) %s" % (
                "(and urls) " if stamp_urls else "",
                "(forced) " if force else "",
                node["path"],
            ))
            (_a, _b, _c, _d, changed) = stamp_availability_on_topic(topic=node, force=force, stamp_urls=stamp_urls)
            if changed:
                strip_counts_from_ancestors(node)
        return node

    def refresh_topic_cache_wrapper_fn(request, cached_nodes={}, force=False, *args, **kwargs):
        """
        Centralized logic for how to refresh the topic cache, for each type of object.

        When the object is desired to be used, this code runs to refresh data,
        balancing between correctness and efficiency.
        """
        if not cached_nodes:
            cached_nodes = {"topics": topic_tools.get_topic_tree()}

        def has_computed_urls(node):
            return "subtitles" in node.get("availability", {}).get("en", {})

        for node in cached_nodes.values():
            if not node:
                continue
            has_children = bool(node.get("children"))

            # Propertes not yet marked
            if node["kind"] == "Video":
                if force or not has_computed_urls(node):
                    recount_videos_and_invalidate_parents(topic_tools.get_parent(node), force=True, stamp_urls=True)

            elif node["kind"] == "Exercise":
                for video in topic_tools.get_related_videos(exercise=node).values():
                    if not has_computed_urls(node):
                        stamp_availability_on_video(video, force=True)  # will be done by force below

            elif node["kind"] == "Topic":
                bottom_layer_topic =  "Topic" not in node["contains"]
                # always run do_video_counts_need_update_question_mark(), to make sure the (internal) counts stay up to date.
                force = do_video_counts_need_update_question_mark() or force or bottom_layer_topic
                recount_videos_and_invalidate_parents(
                    node,
                    force=force,
                    stamp_urls=bottom_layer_topic,
                )

        kwargs.update(cached_nodes)
        return handler(request, *args, **kwargs)
    return refresh_topic_cache_wrapper_fn

# @backend_cache_page
# def splat_handler(request, splat):
#     slugs = filter(lambda x: x, splat.split("/"))
#     topic_tree = topic_tools.get_topic_tree()
#     current_node = topic_tree

#     # Parse out actual current node
#     while current_node:
#         match = [ch for ch in (current_node.get('children') or []) if request.path.startswith(ch["path"])]
#         if len(match) > 1:  # can only happen for leaf nodes (only when one node is blank?)
#             match = [m for m in match if request.path == m["path"]]
#         if not match:
#             raise Http404
#         current_node = match
#         if request.path == current_node["path"]:
#             break

#     # render topic list or playlist of base node
#     if not topic_tools.is_base_leaf(current_node):
#         return topic_handler(request, cached_nodes={"topic_tree": topic_tree})
#         # return topic_handler(request)
#     else:
#         return view_playlist(request, playlist_id=current_node['id'], channel='ka_playlist')


@render_to("distributed/topic.html") # TODO(jamalex): rename topic.html to learn.html
def learn(request):
    """
    Render the all-in-one sidebar navigation/content-viewing app.
    """
    context = {
        "topics_url": "data/%(channel_name)s/topics.json",
        "load_perseus_assets": settings.LOAD_KHAN_RESOURCES,
        "channel": settings.CHANNEL,
    }
    return context


@backend_cache_page
@render_to("distributed/knowledgemap.html")
def exercise_dashboard(request):
    slug = request.GET.get("topic")
    if not slug:
        title = _("Your Knowledge Map")
    elif slug in topic_tools.get_node_cache("Topic"):
        title = _(topic_tools.get_node_cache("Topic")[slug]["title"])
    else:
        raise Http404

    context = {
        "title": title,
        "data_url": "data/" + settings.CHANNEL,
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


# @check_setup_status  # this must appear BEFORE caching logic, so that it isn't blocked by a cache hit
# @backend_cache_page
# @render_to("distributed/homepage.html")
# @refresh_topic_cache
# def homepage(request, topics):
#     """
#     Homepage.
#     """
#     context = topic_context(topics)
#     context.update({
#         "title": "Home",
#     })
#     return context

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
@refresh_topic_cache
def search(request, topics):  # we don't use the topics variable, but this setup will refresh the node cache
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
                if title == query:
                    # Redirect to an exact match
                    return HttpResponseRedirect(node['path'])

                elif len(possible_matches[node_type]) < max_results_per_category and query in title:
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
        return HttpResponseRedirect(set_query_params(reverse("login"), {"next": request.get_full_path()}))

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
