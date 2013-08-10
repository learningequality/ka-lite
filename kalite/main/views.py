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
from django.db.models import Sum
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page

import settings
from config.models import Settings
from control_panel.views import user_management_context
from main import topicdata
from main.models import VideoLog, ExerciseLog, VideoFile
from securesync.api_client import SyncClient
from securesync.models import Facility, FacilityUser,FacilityGroup, Device
from securesync.views import require_admin, facility_required
from utils import topic_tools
from utils.internet import am_i_online, JsonResponse
from utils.jobs import force_job
from utils.decorators import require_admin
from utils.videos import video_connection_is_available


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
        # return HttpResponseNotFound("No valid item found at this address!")
        raise Http404


def check_setup_status(handler):
    def wrapper_fn(request, *args, **kwargs):
        client = SyncClient()
        if not request.is_admin and Facility.objects.count() == 0:
            messages.warning(request, mark_safe(
                "Please <a href='%s?next=%s'>login</a> with the account you created while running the installation script, \
                to complete the setup." % (reverse("login"), reverse("register_public_key"))))
        if request.is_admin:
            if not Settings.get("registered") and client.test_connection() == "success":
                messages.warning(request, mark_safe("Please <a href='%s'>follow the directions to register your device</a>, so that it can synchronize with the central server." % reverse("register_public_key")))
            elif Facility.objects.count() == 0:
                messages.warning(request, mark_safe("Please <a href='%s'>create a facility</a> now. Users will not be able to sign up for accounts until you have made a facility." % reverse("add_facility")))
        return handler(request, *args, **kwargs)
    return wrapper_fn


@cache_page(settings.CACHE_TIME)
@render_to("topic.html")
def topic_handler(request, topic):
    videos    = topic_tools.get_videos(topic)
    exercises = topic_tools.get_exercises(topic)
    topics    = topic_tools.get_live_topics(topic)

    # Get video counts if they'll be used, on-demand only.
    #
    # Check in this order so that the initial counts are always updated
    if topic_tools.video_counts_need_update() or not 'nvideos_local' in topic:
        (topic,_,_) = topic_tools.get_video_counts(topic=topic, videos_path=settings.CONTENT_ROOT)

    my_topics = [dict((k, t[k]) for k in ('title', 'path', 'nvideos_local', 'nvideos_known')) for t in topics]

    context = {
        "topic": topic,
        "title": topic["title"],
        "description": re.sub(r'<[^>]*?>', '', topic["description"] or ""),
        "videos": videos,
        "exercises": exercises,
        "topics": my_topics,
    }
    return context


@cache_page(settings.CACHE_TIME)
@render_to("video.html")
def video_handler(request, video, prev=None, next=None):
    video_exists = VideoFile.objects.filter(pk=video['youtube_id']).exists()

    # If we detect that a video exists, but it's not on disk, then
    #   force the database to update.  No race condition here for saving
    #   progress in a VideoLog: it is not dependent on VideoFile.
    if not video_exists and topic_tools.is_video_on_disk(video['youtube_id']):
        force_job("videoscan")
        video_exists = True

    if not video_exists:
        if request.is_admin:
            # TODO(bcipolli): add a link, with querystring args that auto-checks this video in the topic tree
            messages.warning(request, _("This video was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This video was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This video was not found! You must login as an admin/teacher to download the video."))
    context = {
        "video": video,
        "title": video["title"],
        "video_exists": video_exists,
        "prev": prev,
        "next": next,
    }
    return context


@cache_page(settings.CACHE_TIME)
@render_to("exercise.html")
def exercise_handler(request, exercise):
    """
    Display an exercise
    """
    # Copy related videos (should be small), as we're going to tweak them
    related_videos = [copy.copy(topicdata.NODE_CACHE["Video"].get(key, None)) for key in exercise["related_video_readable_ids"]]

    videos_to_delete = []
    for idx, video in enumerate(related_videos):
        # Remove all videos that were not recognized or 
        #   simply aren't on disk.  
        #   Check on disk is relatively cheap, also executed infrequently
        if not video or not topic_tools.is_video_on_disk(video["youtube_id"]):
            videos_to_delete.append(idx)
            continue

        # Resolve the most related path
        video["path"] = video["paths"][0]  # default value
        for path in video["paths"]:
            if topic_tools.is_sibling({"path": path, "kind": "Video"}, exercise):
                video["path"] = path
                break
        del video["paths"]
    for idx in reversed(videos_to_delete):
        del related_videos[idx]

    context = {
        "exercise": exercise,
        "title": exercise["title"],
        "exercise_template": "exercises/" + exercise["slug"] + ".html",
        "related_videos": related_videos,
    }
    return context

@cache_page(settings.CACHE_TIME)
@render_to("knowledgemap.html")
def exercise_dashboard(request):
    # Just grab the first path, whatever it is
    paths = dict((key, val["paths"][0]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "title": "Knowledge map",
        "exercise_paths": json.dumps(paths),
    }
    return context

@check_setup_status
@cache_page(settings.CACHE_TIME)
@render_to("homepage.html")
def homepage(request):
    # TODO(bcipolli): video counts on the distributed server homepage
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"], topicdata.TOPICS["children"])

    # indexed by integer
    my_topics = [dict([(k, t[k]) for k in ('title', 'path')]) for t in topics]

    context = {
        "title": "Home",
        "topics": my_topics,
        "registered": Settings.get("registered"),
    }
    return context

@require_admin
@render_to("admin_distributed.html")
def easy_admin(request):

    context = {
        "wiki_url" : settings.CENTRAL_WIKI_URL,
        "central_server_host" : settings.CENTRAL_SERVER_HOST,
        "am_i_online": am_i_online(settings.CENTRAL_WIKI_URL, allow_redirects=False),
        "in_a_zone":  Device.get_own_device().get_zone() is not None,
    }
    return context

@require_admin
@render_to("summary_stats.html")
def summary_stats(request):
    # TODO (bcipolli): allow specific stats to be requested (more efficient)

    context = {
        "video_stats" : get_stats(("total_video_views","total_video_time","total_video_points")),
        "exercise_stats": get_stats(("total_exercise_attempts","total_exercise_points","total_exercise_status")),
        "user_stats": get_stats(("total_users",)),
        "group_stats": get_stats(("total_groups",)),
    }
    return context


def get_stats(stat_names):
    """Given a list of stat names, return a dictionary of stat values.
    For efficiency purposes, best to request all related stats together.
    In low-memory conditions should group requests by common source (video, exercise, user, group), but otherwise separate

Available stats:
    video:    total_video_views, total_video_time, total_video_points
    exercise: total_exercise_attempts, total_exercise_points, total_exercise_status
    users:    total_users
    groups:   total_groups
    """

    val = {}
    for stat_name in stat_names:

        # Total time from videos
        if stat_name == "total_video_views":
            val[stat_name] = VideoLog.objects.count()

        # Total time from videos
        elif stat_name == "total_video_time":
            val[stat_name] = VideoLog.objects.aggregate(Sum("total_seconds_watched"))['total_seconds_watched__sum'] or 0

        elif stat_name == "total_video_points":
            val[stat_name] = VideoLog.objects.aggregate(Sum("points"))['points__sum'] or 0

        elif stat_name == "total_exercise_attempts":
            val[stat_name] = ExerciseLog.objects.aggregate(Sum("attempts"))['attempts__sum'] or 0

        elif stat_name == "total_exercise_points":
            val[stat_name] = ExerciseLog.objects.aggregate(Sum("points"))['points__sum'] or 0

        elif stat_name == "total_exercise_status":
            val[stat_name] = {
                "struggling": ExerciseLog.objects.aggregate(Sum("struggling"))['struggling__sum'] or 0,
                "completed": ExerciseLog.objects.aggregate(Sum("complete"))['complete__sum'] or 0,
            }
            val[stat_name]["inprog"] = ExerciseLog.objects.count() - sum([stat for stat in val[stat_name].values()])

        elif stat_name == "total_users":
            val[stat_name] = FacilityUser.objects.count()

        elif stat_name == "total_groups":
            val[stat_name] = FacilityGroup.objects.count()

        else:
            raise Exception("Unknown stat requested: %s" % stat_name)

    return val

@require_admin
@render_to("video_download.html")
def update(request):
    call_command("videoscan")  # Could potentially be very slow, blocking request.
    force_job("videodownload", "Download Videos")
    force_job("subtitledownload", "Download Subtitles")
    language_lookup = topicdata.LANGUAGE_LOOKUP
    language_list = topicdata.LANGUAGE_LIST
    default_language = Settings.get("subtitle_language") or "en"
    if default_language not in language_list:
        language_list.append(default_language)
    languages = [{"id": key, "name": language_lookup[key]} for key in language_list]
    languages = sorted(languages, key=lambda k: k["name"])

    am_i_online = video_connection_is_available()
    if not am_i_online:
        messages.warning(request, _("No internet connection was detected.  You must be online to download videos or subtitles."))

    context = {
        "languages": languages,
        "default_language": default_language,
        "am_i_online": am_i_online,
    }
    return context


@require_admin
@facility_required
@render_to("current_users.html")
def user_list(request,facility):
    return user_management_context(
        request=request,
        facility_id=facility.id,
        group_id=request.REQUEST.get("group",""),
        page=request.REQUEST.get("page","1"),
    )


@require_admin
def zone_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()
    if zone:
        return HttpResponseRedirect(reverse("zone_management", kwargs={"org_id": "", "zone_id": zone.pk}))
    else:
        raise Http404(_("This device is not on any zone."))

@require_admin
def device_redirect(request):
    """
    Dummy view to generate a helpful dynamic redirect to interface with 'control_panel' app
    """
    device = Device.get_own_device()
    zone = device.get_zone()
    if zone:
        return HttpResponseRedirect(reverse("device_management", kwargs={"org_id": "", "zone_id": zone.pk, "device_id": device.pk}))
    else:
        raise Http404(_("This device is not on any zone."))


def handler_403(request, *args, **kwargs):
    context = RequestContext(request)
    #message = None  # Need to retrieve, but can't figure it out yet.

    if request.is_ajax():
        return JsonResponse({ "error": "You must be logged in with an account authorized to view this page." }, status=403)
    else:
        messages.error(request, mark_safe(_("You must be logged in with an account authorized to view this page..")))
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
