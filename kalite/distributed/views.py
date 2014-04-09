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

from .caching import backend_cache_page
from fle_utils.django_utils import is_loopback_connection
from fle_utils.internet import JsonResponse, JsonResponseMessageError, get_ip_addresses, set_query_params, backend_cache_page
from kalite.facility.models import Facility, FacilityUser,FacilityGroup
from kalite.i18n import select_best_available_language
from kalite.main import topic_tools
from kalite.main.models import VideoLog, ExerciseLog
from kalite.main.topic_tools import get_ancestor, get_parent, get_neighbor_nodes, get_topic_tree
from kalite.shared.decorators import require_admin
from kalite.updates import stamp_availability_on_topic, stamp_availability_on_video, do_video_counts_need_update_question_mark
from securesync.api_client import BaseClient
from securesync.models import Device, SyncSession


def check_setup_status(handler):
    """
    Decorator for validating that KA Lite post-install setup has completed.
    NOTE that this decorator must appear before the backend_cache_page decorator,
    so that it is run even when there is a cache hit.
    """
    def wrapper_fn(request, *args, **kwargs):
        if request.is_admin:
            # TODO(bcipolli): move this to the client side?
            if not request.session["registered"] and BaseClient().test_connection() == "success":
                # Being able to register is more rare, so prioritize.
                messages.warning(request, mark_safe("Please <a href='%s'>follow the directions to register your device</a>, so that it can synchronize with the central server." % reverse("register_public_key")))
            elif not request.session["facility_exists"]:
                messages.warning(request, mark_safe("Please <a href='%s'>create a facility</a> now. Users will not be able to sign up for accounts until you have made a facility." % reverse("add_facility")))

        elif not request.is_logged_in:
            if not request.session["registered"] and BaseClient().test_connection() == "success":
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
    return wrapper_fn


def refresh_topic_cache(handler, force=False):

    def strip_counts_from_ancestors(node):
        """
        Remove relevant counts from all ancestors
        """
        for ancestor_id in node.get("ancestor_ids", []):
            ancestor = get_ancestor(node, ancestor_id)
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
                    recount_videos_and_invalidate_parents(get_parent(node), force=True, stamp_urls=True)

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

@backend_cache_page
def splat_handler(request, splat):
    slugs = filter(lambda x: x, splat.split("/"))
    current_node = topic_tools.get_topic_tree()
    while current_node:
        match = [ch for ch in (current_node.get('children') or []) if request.path.startswith(ch["path"])]
        if len(match) > 1:  # can only happen for leaf nodes (only when one node is blank?)
            match = [m for m in match if request.path == m["path"]]
        if not match:
            raise Http404
        current_node = match[0]
        if request.path == current_node["path"]:
            break

    if current_node["kind"] == "Topic":
        return topic_handler(request, cached_nodes={"topic": current_node})
    elif current_node["kind"] == "Video":
        prev, next = get_neighbor_nodes(current_node, neighbor_kind=current_node["kind"])
        return video_handler(request, cached_nodes={"video": current_node, "prev": prev, "next": next})
    elif current_node["kind"] == "Exercise":
        cached_nodes = topic_tools.get_related_videos(current_node, limit_to_available=False)
        cached_nodes["exercise"] = current_node
        cached_nodes["prev"], cached_nodes["next"] = get_neighbor_nodes(current_node, neighbor_kind=current_node['kind'])
        return exercise_handler(request, cached_nodes=cached_nodes)
    else:
        raise Http404


@backend_cache_page
@render_to("distributed/topic.html")
@refresh_topic_cache
def topic_handler(request, topic):
    return topic_context(topic)


def topic_context(topic):
    """
    Given a topic node, create all context related to showing that topic
    in a template.
    """
    videos    = topic_tools.get_videos(topic)
    exercises = topic_tools.get_exercises(topic)
    topics    = topic_tools.get_live_topics(topic)
    my_topics = [dict((k, t[k]) for k in ('title', 'path', 'nvideos_local', 'nvideos_known', 'nvideos_available', 'available')) for t in topics]

    exercises_path = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
    exercise_langs = dict([(exercise["id"], ["en"]) for exercise in exercises])

    # Determine what exercises (and languages) are available
    exercise_all_lang_codes = os.listdir(exercises_path) if os.path.exists(exercises_path) else []
    exercise_all_lang_codes = set(exercise_all_lang_codes) - set(["test"])
    for lang_code in exercise_all_lang_codes:  # hard-code out test
        loc_path = os.path.join(exercises_path, lang_code)
        if not os.path.isdir(loc_path):
            continue

        for exercise in exercises:
            ex_path = os.path.join(loc_path, "%s.html" % exercise["id"])
            if not os.path.exists(ex_path):
                continue
            exercise_langs[exercise["id"]].append(lang_code)


    context = {
        "topic": topic,
        "title": topic["title"],
        "description": re.sub(r'<[^>]*?>', '', topic["description"] or ""),
        "videos": videos,
        "exercises": exercises,
        "exercise_langs": exercise_langs,
        "topics": my_topics,
    }
    return context


@backend_cache_page
@render_to("distributed/video.html")
@refresh_topic_cache
def video_handler(request, video, format="mp4", prev=None, next=None):

    if not video["available"]:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this video in the topic tree
            messages.warning(request, _("This video was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This video was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This video was not found! You must login as an admin/teacher to download the video."))

    # Fallback mechanism
    available_urls = dict([(lang, avail) for lang, avail in video["availability"].iteritems() if avail["on_disk"]])
    if video["available"] and not available_urls:
        vid_lang = "en"
        messages.success(request, "Got video content from %s" % video["availability"]["en"]["stream"])
    else:
        vid_lang = select_best_available_language(request.language, available_codes=available_urls.keys())


    context = {
        "video": video,
        "title": video["title"],
        "num_videos_available": len(video["availability"]),
        "selected_language": vid_lang,
        "video_urls": video["availability"].get(vid_lang),
        "subtitle_urls": video["availability"].get(vid_lang, {}).get("subtitles"),
        "prev": prev,
        "next": next,
        "backup_vids_available": bool(settings.BACKUP_VIDEO_SOURCE),
        "use_mplayer": settings.USE_MPLAYER and is_loopback_connection(request),
    }
    return context


@backend_cache_page
@render_to("distributed/exercise.html")
@refresh_topic_cache
def exercise_handler(request, exercise, prev=None, next=None, **related_videos):
    """
    Display an exercise
    """
    lang = request.session[settings.LANGUAGE_COOKIE_NAME]
    exercise_root = os.path.join(settings.KHAN_EXERCISES_DIRPATH, "exercises")
    exercise_file = exercise["slug"] + ".html"
    exercise_template = exercise_file
    exercise_localized_template = os.path.join(lang, exercise_file)

    # Get the language codes for exercise teplates that exist
    exercise_path = partial(lambda lang, slug, eroot: os.path.join(eroot, lang, slug + ".html"), slug=exercise["slug"], eroot=exercise_root)
    code_filter = partial(lambda lang, eroot, epath: os.path.isdir(os.path.join(eroot, lang)) and os.path.exists(epath(lang)), eroot=exercise_root, epath=exercise_path)
    available_langs = set(["en"] + [lang_code for lang_code in os.listdir(exercise_root) if code_filter(lang_code)])

    # Return the best available exercise template
    exercise_lang = select_best_available_language(request.language, available_codes=available_langs)
    if exercise_lang == "en":
        exercise_template = exercise_file
    else:
        exercise_template = exercise_path(exercise_lang)[(len(exercise_root) + 1):]

    context = {
        "exercise": exercise,
        "title": exercise["title"],
        "exercise_template": exercise_template,
        "exercise_lang": exercise_lang,
        "related_videos": [v for v in related_videos.values() if v["available"]],
        "prev": prev,
        "next": next,
    }
    return context


@backend_cache_page
@render_to("distributed/knowledgemap.html")
def exercise_dashboard(request):
    slug = request.GET.get("topic")
    if not slug:
        title = _("Your Knowledge Map")
    elif slug in topic_tools.get_node_cache("Topic"):
        title = _(topic_tools.get_node_cache("Topic")[slug][0]["title"])
    else:
        raise Http404

    context = {
        "title": title,
    }
    return context


def watch_home(request):
    """Dummy wrapper function for topic_handler with url=/"""
    return topic_handler(request, cached_nodes={"topic": get_topic_tree()})


@check_setup_status  # this must appear BEFORE caching logic, so that it isn't blocked by a cache hit
@backend_cache_page
@render_to("distributed/homepage.html")
@refresh_topic_cache
def homepage(request, topics):
    """
    Homepage.
    """
    context = topic_context(topics)
    context.update({
        "title": "Home",
    })
    return context

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
        "central_server_host" : settings.CENTRAL_SERVER_HOST,
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
    if zone:
        return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": zone.pk}))
    else:
        return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": "None"}))

@require_admin
def device_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()

    return HttpResponseRedirect(reverse("device_management", kwargs={"zone_id": zone.pk if zone else None, "device_id": device.pk}))

JS_CATALOG_CACHE = {}
def javascript_catalog_cached(request):
    global JS_CATALOG_CACHE
    lang = request.session['default_language']
    if lang in JS_CATALOG_CACHE:
        logging.debug('Using js translation catalog cache for %s' % lang)
        src = JS_CATALOG_CACHE[lang]
        return HttpResponse(src, 'text/javascript')
    else:
        logging.debug('Generating js translation catalog for %s' % lang)
        resp = javascript_catalog(request, 'djangojs', settings.INSTALLED_APPS)
        src = resp.content
        JS_CATALOG_CACHE[lang] = src
        return resp

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
            for nodearr in node_dict.values():
                node = nodearr[0]
                title = _(node['title']).lower()  # this could be done once and stored.
                if title == query:
                    # Redirect to an exact match
                    return HttpResponseRedirect(node['path'])

                elif len(possible_matches[node_type]) < max_results_per_category and query in title:
                    # For efficiency, don't do substring matches when we've got lots of results
                    possible_matches[node_type].append(node)

            hit_max[node_type] = len(possible_matches[node_type]) == max_results_per_category

    return {
        'title': _("Search results for '%s'") % (query if query else ""),
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


def handler_404(request):
    return HttpResponseNotFound(render_to_string("distributed/404.html", {}, context_instance=RequestContext(request)))


def handler_500(request):
    errortype, value, tb = sys.exc_info()
    context = {
        "errortype": errortype.__name__,
        "value": unicode(value),
    }
    return HttpResponseServerError(render_to_string("distributed/500.html", context, context_instance=RequestContext(request)))
