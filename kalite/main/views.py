import re, json
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.core.urlresolvers import reverse
from annoying.decorators import render_to
import settings
from settings import slug_key, title_key
from main import topicdata
from django.contrib import messages
from securesync.views import require_admin, facility_required

from securesync.models import Facility, FacilityGroup

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

    if request.user.is_authenticated():
        messages.warning(request, "Note: You're logged in as an admin (not a facility user), so your exercise progress and points won't be saved.")
    elif not request.is_logged_in:
        messages.warning(request, "Friendly reminder: You are not currently logged in, so your exercise progress and points won't be saved.")

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
    
@render_to("homepage.html")
def homepage(request):
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"], topicdata.TOPICS["children"])
    context = {
        "title": "Home",
        "topics": topics,
    }
    return context
        
@require_admin
@render_to("video_download.html")
def video_download(request):
#    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"], settings.TOPICS["children"])
    context = {
#        "title": "Home",
#        "topics": topics,
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
    return {}
    
@render_to("404_central.html")
def central_404_handler(request):
    return {}
    
@render_to("500_central.html")
def central_500_handler(request):
    return {}