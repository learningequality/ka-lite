import re, json, sys
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.management import call_command
from django.core.urlresolvers import reverse
from annoying.decorators import render_to
from annoying.functions import get_object_or_None
import settings
from settings import slug_key, title_key
from main import topicdata
from django.contrib import messages
from securesync.views import require_admin, facility_required
from config.models import Settings
from securesync.models import Facility, FacilityGroup
from models import FacilityUser, VideoLog, ExerciseLog, VideoFile
from django.utils.safestring import mark_safe
from config.models import Settings
from securesync.api_client import SyncClient
from django.contrib import messages
from utils.jobs import force_job
from django.utils.translation import ugettext as _

def splat_handler(request, splat):
    slugs = filter(lambda x: x, splat.split("/"))
    current_node = topicdata.TOPICS
    seeking = "Topic"
    for slug in slugs:
        if slug == "v":
            seeking = "Video"
        elif slug == "e":
            seeking = "Exercise"
        else:
            children = [child for child in current_node['children'] if child['kind'] == seeking]
            if not children:
                # return HttpResponseNotFound("No children of type '%s' found for node '%s'!" %
                #     (seeking, current_node[title_key[current_node['kind']]]))
                raise Http404
            match = None
            prev = None
            next = None
            for child in children:
                if match:
                    next = child
                    break
                if child[slug_key[seeking]] == slug:
                    match = child
                else:
                    prev = child
            if not match:
                # return HttpResponseNotFound("Child with slug '%s' of type '%s' not found in node '%s'!" %
                #     (slug, seeking, current_node[title_key[current_node['kind']]]))
                raise Http404
            current_node = match
    if current_node["kind"] == "Topic":
        return topic_handler(request, current_node)
    if current_node["kind"] == "Video":
        return video_handler(request, video=current_node, prev=prev, next=next)
    if current_node["kind"] == "Exercise":
        return exercise_handler(request, current_node)
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

@render_to("topic.html")
def topic_handler(request, topic):
    videos = filter(lambda node: node["kind"] == "Video", topic["children"])
    exercises = filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])
    context = {
        "topic": topic,
        "title": topic[title_key["Topic"]],
        "description": re.sub(r'<[^>]*?>', '', topic["description"] or ""),
        "videos": videos,
        "exercises": exercises,
        "topics": topics,
    }
    return context
    
@render_to("video.html")
def video_handler(request, video, prev=None, next=None):
    if not VideoFile.objects.filter(pk=video['youtube_id']).exists():
        if request.is_admin:
            messages.warning(request, _("This video was not found! You can download it by going to the Update page."))
        elif request.is_logged_in:
            messages.warning(request, _("This video was not found! Please contact your teacher or an admin to have it downloaded."))
        elif not request.is_logged_in:
            messages.warning(request, _("This video was not found! You must login as an admin/teacher to download the video."))
    elif request.user.is_authenticated():
        messages.warning(request, _("Note: You're logged in as an admin (not as a student/teacher), so your video progress and points won't be saved."))
    elif not request.is_logged_in:
        messages.warning(request, _("Friendly reminder: You are not currently logged in, so your video progress and points won't be saved."))
    context = {
        "video": video,
        "title": video[title_key["Video"]],
        "prev": prev,
        "next": next,
    }
    return context
    
@render_to("exercise.html")
def exercise_handler(request, exercise):
    related_videos = [topicdata.NODE_CACHE["Video"][key] for key in exercise["related_video_readable_ids"]]
    
    if request.user.is_authenticated():
        messages.warning(request, _("Note: You're logged in as an admin (not as a student/teacher), so your exercise progress and points won't be saved."))
    elif not request.is_logged_in:
        messages.warning(request, _("Friendly reminder: You are not currently logged in, so your exercise progress and points won't be saved."))

    context = {
        "exercise": exercise,
        "title": exercise[title_key["Exercise"]],
        "exercise_template": "exercises/" + exercise[slug_key["Exercise"]] + ".html",
        "related_videos": related_videos,
    }
    return context

@render_to("knowledgemap.html")
def exercise_dashboard(request):
    paths = dict((key, val["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "title": "Knowledge map",
        "exercise_paths": json.dumps(paths),
    }
    return context
    
@check_setup_status
@render_to("homepage.html")
def homepage(request):
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"], topicdata.TOPICS["children"])
    context = {
        "title": "Home",
        "topics": topics,
        "registered": Settings.get("registered"),
    }
    return context
        
@require_admin
@render_to("video_download.html")
def update(request):
    call_command("videoscan")
    force_job("videodownload", "Download Videos")
    force_job("subtitledownload", "Download Subtitles")
    language_lookup = topicdata.LANGUAGE_LOOKUP
    language_list = topicdata.LANGUAGE_LIST
    default_language = Settings.get("subtitle_language") or "en"
    if default_language not in language_list:
        language_list.append(default_language)
    languages = [{"id": key, "name": language_lookup[key]} for key in language_list]
    languages = sorted(languages, key=lambda k: k["name"])
    context = {
        "languages": languages,
        "default_language": default_language,
    }
    return context

@require_admin
@facility_required
@render_to("coach_reports.html")
def coach_reports(request, facility):
    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    groups = FacilityGroup.objects.filter(facility=facility)
    paths = dict((key, val["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "facility": facility,
        "groups": groups,
        "topics": topics,
        "exercise_paths": json.dumps(paths),
    }
    topic = request.GET.get("topic", "")
    group = request.GET.get("group", "")
    if group and topic and re.match("^[\w\-]+$", topic):
        exercises = json.loads(open("%stopicdata/%s.json" % (settings.DATA_PATH, topic)).read())
        exercises = sorted(exercises, key=lambda e: (e["h_position"], e["v_position"]))
        context["exercises"] = [{
            "display_name": ex["display_name"],
            "description": ex["description"],
            "short_display_name": ex["short_display_name"],
            "path": topicdata.NODE_CACHE["Exercise"][ex["name"]]["path"],
        } for ex in exercises]
        users = get_object_or_404(FacilityGroup, pk=group).facilityuser_set.order_by("first_name", "last_name")
        context["students"] = [{
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "exercise_logs": [get_object_or_None(ExerciseLog, user=user, exercise_id=ex["name"]) for ex in exercises],
        } for user in users]
    return context

@require_admin
@facility_required
@render_to("current_users.html")
def user_list(request,facility):
    groups = FacilityGroup.objects.filter(facility=facility)
    group = request.GET.get("group", "")
    page = request.GET.get("page","")
    user_list = get_object_or_404(FacilityGroup, pk=group).defer("facility","is_teacher","notes","password").facilityuser_set.order_by("first_name", "last_name")
    paginator = Paginator(user_list, 25)
    try:
        users = paginator.page(page)
    except PageNotAnInteger:
        users = paginator.page(1)
    except EmptyPage:
        users = paginator.page(paginator.num_pages)
    context["users"] = users
    context["groups"] = groups
    return context

def distributed_404_handler(request):
    return HttpResponseNotFound(render_to_string("404_distributed.html", {}, context_instance=RequestContext(request)))

def distributed_500_handler(request):
    errortype, value, tb = sys.exc_info()
    context = {
        "errortype": errortype.__name__,
        "value": str(value),
    }
    return HttpResponseServerError(render_to_string("500_distributed.html", context, context_instance=RequestContext(request)))
    
def central_404_handler(request):
    return HttpResponseNotFound(render_to_string("404_central.html", {}, context_instance=RequestContext(request)))
    
def central_500_handler(request):
    return HttpResponseServerError(render_to_string("500_central.html", {}, context_instance=RequestContext(request)))