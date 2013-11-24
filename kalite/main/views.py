import copy
import json
import re
import sys
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db.models import Sum, Count
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import settings
from config.models import Settings
from control_panel.views import user_management_context
from main import topicdata
from main.models import VideoLog, ExerciseLog
from securesync.api_client import BaseClient
from securesync.models import Facility, FacilityUser,FacilityGroup, Device
from securesync.views import require_admin, facility_required
from settings import LOG as logging
from shared import topic_tools
from shared.caching import backend_cache_page
from shared.decorators import require_admin
from shared.jobs import force_job
from shared.videos import get_video_urls, is_video_on_disk, video_counts_need_update, get_video_counts
from utils.internet import is_loopback_connection, JsonResponse

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
                redirect_url = reverse("add_facility")
            else:
                redirect_url = None

            if redirect_url:
                messages.warning(request, mark_safe(
                    "Please <a href='%s?next=%s'>login</a> with the account you created while running the installation script, \
                    to complete the setup." % (reverse("login"), redirect_url)))

        return handler(request, *args, **kwargs)
    return wrapper_fn


@backend_cache_page
def splat_handler(request, splat):
    slugs = filter(lambda x: x, splat.split("/"))
    current_node = topicdata.TOPICS
    seeking = "Topic" # search for topics, until we find videos or exercise
    for slug in slugs:
        # towards the end of the url, we switch from seeking a topic node
        #   to the particular type of node in the tree
        for kind, kind_slug in topic_tools.kind_slugs.items():
            if slug == kind_slug.split("/")[0]:
                seeking = kind
                break

        # match each step in the topics hierarchy, with the url slug.
        else:
            children = [child for child in current_node['children'] if child['kind'] == seeking]
            if not children:
                raise Http404
            match = None
            prev = None
            next = None
            for child in children:
                if match:
                    next = child
                    break
                if child["slug"] == slug:
                    match = child
                else:
                    prev = child
            if not match:
                raise Http404
            current_node = match
    if current_node["kind"] == "Topic":
        return topic_handler(request, current_node)
    elif current_node["kind"] == "Video":
        return video_handler(request, video=current_node, prev=prev, next=next)
    elif current_node["kind"] == "Exercise":
        return exercise_handler(request, current_node)
    else:
        raise Http404


@backend_cache_page
@render_to("topic.html")
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

    # Get video counts if they'll be used, on-demand only.
    #
    # Check in this order so that the initial counts are always updated
    if video_counts_need_update() or not 'nvideos_local' in topic:
        (topic,_,_) = get_video_counts(topic=topic, videos_path=settings.CONTENT_ROOT)

    my_topics = [dict((k, t[k]) for k in ('title', 'path', 'nvideos_local', 'nvideos_known')) for t in topics]

    context = {
        "topic": topic,
        "title": topic["title"],
        "description": re.sub(r'<[^>]*?>', '', topic["description"] or ""),
        "videos": videos,
        "exercises": exercises,
        "topics": my_topics,
        "backup_vids_available": bool(settings.BACKUP_VIDEO_SOURCE),
    }
    return context


@backend_cache_page
@render_to("video.html")
def video_handler(request, video, format="mp4", prev=None, next=None):

    video_on_disk = is_video_on_disk(video['youtube_id'])
    video_exists = video_on_disk or bool(settings.BACKUP_VIDEO_SOURCE)

    if not video_exists:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this video in the topic tree
            messages.warning(request, _("This video was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This video was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This video was not found! You must login as an admin/teacher to download the video."))

    video["stream_type"] = "video/%s" % format

    if video_exists and not video_on_disk:
        messages.success(request, "Got video content from %s" % video["stream_url"])

    context = {
        "video": video,
        "title": video["title"],
        "prev": prev,
        "next": next,
        "backup_vids_available": bool(settings.BACKUP_VIDEO_SOURCE),
        "use_mplayer": settings.USE_MPLAYER and is_loopback_connection(request),
    }
    return context


@backend_cache_page
@render_to("exercise.html")
def exercise_handler(request, exercise):
    """
    Display an exercise
    """
    # Find related videos
    related_videos = {}
    for slug in exercise["related_video_slugs"]:
        video_nodes = topicdata.NODE_CACHE["Video"].get(topicdata.SLUG2ID_MAP.get(slug), None)

        # Make sure the IDs are recognized, and are available.
        if not video_nodes:
            continue
        if not video_nodes[0].get("on_disk", False) and not settings.BACKUP_VIDEO_SOURCE:
            continue

        # Search for a sibling video node to add to related exercises.
        for video in video_nodes:
            if topic_tools.is_sibling({"path": video["path"], "kind": "Video"}, exercise):
                related_videos[slug] = video
                break

        # failed to find a sibling; just choose the first one.
        if slug not in related_videos:
            related_videos[slug] = video_nodes[0]

    context = {
        "exercise": exercise,
        "title": exercise["title"],
        "exercise_template": "exercises/" + exercise["slug"] + ".html",
        "related_videos": related_videos.values(),
    }
    return context


@backend_cache_page
@render_to("knowledgemap.html")
def exercise_dashboard(request):
    # Just grab the first path, whatever it is
    paths = dict((key, val[0]["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].iteritems())
    slug = request.GET.get("topic")

    context = {
        "title": topicdata.NODE_CACHE["Topic"][slug][0]["title"] if slug else _("Your Knowledge Map"),
        "exercise_paths": json.dumps(paths),
    }
    return context

@check_setup_status  # this must appear BEFORE caching logic, so that it isn't blocked by a cache hit
@backend_cache_page
@render_to("homepage.html")
def homepage(request):
    context = topic_context(topicdata.TOPICS)
    context.update({
        "title": "Home",
        "backup_vids_available": bool(settings.BACKUP_VIDEO_SOURCE),
    })
    return context

@require_admin
@check_setup_status
@render_to("admin_distributed.html")
def easy_admin(request):

    context = {
        "wiki_url" : settings.CENTRAL_WIKI_URL,
        "central_server_host" : settings.CENTRAL_SERVER_HOST,
        "in_a_zone":  Device.get_own_device().get_zone() is not None,
        "clock_set": settings.ENABLE_CLOCK_SET,
    }
    return context


@require_admin
@facility_required
@render_to("current_users.html")
def user_list(request, facility):

    # Use default group
    group_id = request.REQUEST.get("group")
    if not group_id:
        groups = FacilityGroup.objects \
            .annotate(Count("facilityuser")) \
            .filter(facilityuser__count__gt=0)
        ngroups = groups.count()
        ngroups += int(FacilityUser.objects.filter(group__isnull=True).count() > 0)
        if ngroups == 1:
            group_id = groups[0].id if groups.count() else "Ungrouped"

    context = user_management_context(
        request=request,
        facility_id=facility.id,
        group_id=group_id,
        page=request.REQUEST.get("page","1"),
    )
    context.update({
        "singlefacility": Facility.objects.count() == 1,
    })
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
        return HttpResponseRedirect(reverse("zone_management", kwargs={"zone_id": None}))

@require_admin
def device_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()
    if zone:
        return HttpResponseRedirect(reverse("device_management", kwargs={"zone_id": zone.pk, "device_id": device.pk}))
    else:
        raise Http404(_("This device is not on any zone."))

@render_to('search_page.html')
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
        for node_type, node_dict in topicdata.NODE_CACHE.iteritems():
            if category and node_type != category:
                # Skip categories that don't match (if specified)
                continue

            possible_matches[node_type] = []  # make dict only for non-skipped categories
            for nodearr in node_dict.values():
                node = nodearr[0]
                title = node['title'].lower()  # this could be done once and stored.
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

def handler_403(request, *args, **kwargs):
    context = RequestContext(request)
    #message = None  # Need to retrieve, but can't figure it out yet.

    if request.is_ajax():
        return JsonResponse({ "error": "You must be logged in with an account authorized to view this page." }, status=403)
    else:
        messages.error(request, mark_safe(_("You must be logged in with an account authorized to view this page.")))
        return HttpResponseRedirect(reverse("login") + "?next=" + request.path)


def handler_404(request):
    return HttpResponseNotFound(render_to_string("404.html", {}, context_instance=RequestContext(request)))


def handler_500(request):
    errortype, value, tb = sys.exc_info()
    context = {
        "errortype": errortype.__name__,
        "value": str(value),
    }
    return HttpResponseServerError(render_to_string("500.html", context, context_instance=RequestContext(request)))
