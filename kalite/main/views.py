import re, json, sys
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.core.management import call_command
from django.core.urlresolvers import reverse
from annoying.decorators import render_to
import settings
from settings import slug_key, title_key
from main import topicdata
from django.contrib import messages
from securesync.views import require_admin, facility_required
from config.models import Settings
from securesync.models import Facility, FacilityGroup
from django.utils.safestring import mark_safe
from config.models import Settings
from securesync.api_client import SyncClient
from django.contrib import messages
from utils.jobs import force_job

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
            messages.warning(request, mark_safe("Please <a href='%s'>login</a> with the account you created in the installation script, to complete the setup." % reverse("login")))
        if request.is_admin:
            if not Settings.get("registered") and client.test_connection() == "success":
                messages.warning(request, mark_safe("Please <a href='%s'>follow the directions to register your device</a>, so that it can synchronize with the central server." % reverse("register_public_key")))
            elif Facility.objects.count() == 0:
                messages.warning(request, mark_safe("Please <a href='%s'>create a facility</a>. Users will not be able to sign up until you do so." % reverse("add_facility")))
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
    if request.user.is_authenticated():
        messages.warning(request, "Note: You're logged in as an admin (not a facility user), so your video progress and points won't be saved.")
    elif not request.is_logged_in:
        messages.warning(request, "Friendly reminder: You are not currently logged in, so your video progress and points won't be saved.")
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
    
    referURL = request.META["HTTP_REFERER"]
    
    if request.user.is_authenticated():
        messages.warning(request, "Note: You're logged in as an admin (not a facility user), so your exercise progress and points won't be saved.")
    elif not request.is_logged_in:
        messages.warning(request, "Friendly reminder: You are not currently logged in, so your exercise progress and points won't be saved.")

    context = {
        "exercise": exercise,
        "title": exercise[title_key["Exercise"]],
        "exercise_template": "exercises/" + exercise[slug_key["Exercise"]] + ".html",
        "related_videos": related_videos,
        "referURL": referURL,
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
    languages = [{"id":key,"name":language_lookup[key]} for key in language_list]
    languages = sorted(languages, key = lambda k: k["name"])
    context = {
        "languages": languages,
        "default_language": default_language,
    }
    return context

@require_admin
@facility_required
@render_to("teacher_panel.html")
def teacher_panel(request,facility):
    topics = topicdata.EXERCISE_TOPICS["topics"].values()
    topics = sorted(topics, key = lambda k: (k["y"], k["x"]))
    groups = FacilityGroup.objects.filter(facility=facility)
    context = {
        "facility": facility,
        "groups": groups,
        "topics": topics,
    }
    return context
        
@render_to("404_distributed.html")
def distributed_404_handler(request):
    return {}
    
@render_to("500_distributed.html")
def distributed_500_handler(request):
    errortype, value, tb = sys.exc_info()
    return {
        "errortype": errortype.__name__,
        "value": str(value),
    }
    
@render_to("404_central.html")
def central_404_handler(request):
    return {}
    
@render_to("500_central.html")
def central_500_handler(request):
    return {}