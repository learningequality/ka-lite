import re, json, sys, logging
from annoying.decorators import render_to
from annoying.functions import get_object_or_None

from django.http import HttpResponse, HttpResponseNotFound, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404, redirect, get_list_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.utils.safestring import mark_safe
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.cache import cache_control
from django.views.decorators.cache import cache_page

import settings
from settings import slug_key, title_key
from main import topicdata
from securesync.views import require_admin, facility_required
from config.models import Settings
from securesync.models import Facility, FacilityUser,FacilityGroup
from models import VideoLog, ExerciseLog, VideoFile
from config.models import Settings
from securesync.api_client import SyncClient
from utils.jobs import force_job


def splat_handler(request, splat):
    slugs = filter(lambda x: x, splat.split("/"))
    current_node = topicdata.TOPICS
    seeking = "Topic" # search for topics, until we find videos or exercise
    for slug in slugs:
        # towards the end of the url, we switch from seeking a topic node
        #   to the particular type of node in the tree
        if slug == "v":
            seeking = "Video"
        elif slug == "e":
            seeking = "Exercise"
            
        # match each step in the topics hierarchy, with the url slug.
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
    videos = filter(lambda node: node["kind"] == "Video", topic["children"])
    exercises = filter(lambda node: node["kind"] == "Exercise" and node["live"], topic["children"])
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"] and "Video" in node["contains"], topic["children"])
    
    my_topics = []
    for t in topics:
        my_topics.append({ 'title': t['title'], 'path': t['path'] })
        
    context = {
        "topic": topic,
        "title": topic[title_key["Topic"]],
        "description": re.sub(r'<[^>]*?>', '', topic["description"] or ""),
        "videos": videos,
        "exercises": exercises,
        "topics": my_topics,
    }
    return context
    

@cache_page(settings.CACHE_TIME)
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
    

@cache_page(settings.CACHE_TIME)
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

@cache_page(settings.CACHE_TIME)
@render_to("knowledgemap.html")
def exercise_dashboard(request):
    paths = dict((key, val["path"]) for key, val in topicdata.NODE_CACHE["Exercise"].items())
    context = {
        "title": "Knowledge map",
        "exercise_paths": json.dumps(paths),
    }
    return context
    
@check_setup_status
@cache_page(settings.CACHE_TIME)
@render_to("homepage.html")
def homepage(request):
    topics = filter(lambda node: node["kind"] == "Topic" and not node["hide"], topicdata.TOPICS["children"])
    
    my_topics = []
    for t in topics:
        my_topics.append({ 'title': t['title'], 'path': t['path'] })

    context = {
        "title": "Home",
        "topics": my_topics,
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
    GETParam = request.GET.copy()
    if group:
        if group == "Ungrouped":
            user_list = FacilityUser.objects.filter(facility=facility,group__isnull=True)
        else:
            user_list = get_object_or_404(FacilityGroup, pk=group).facilityuser_set.order_by("first_name", "last_name")
        paginator = Paginator(user_list, 25)
        try:
            users = paginator.page(page)
        except PageNotAnInteger:
            users = paginator.page(1)
        except EmptyPage:
            users = paginator.page(paginator.num_pages)
    else:
        group = ''
        users = []
    if users:
        if users.has_previous():
            prevGETParam = GETParam.copy()
            prevGETParam["page"] = users.previous_page_number()
            previous_page_url = "?" + prevGETParam.urlencode()
        else:
            previous_page_url = ""
        if users.has_next():
            nextGETParam = GETParam.copy()
            nextGETParam["page"] = users.next_page_number()
            next_page_url = "?" + nextGETParam.urlencode()
        else:
            next_page_url = ""
    context = {
        "facility": facility,
        "users": users,
        "groups": groups,
    }
    if users:
        context["pageurls"] = {"next_page": next_page_url, "prev_page": previous_page_url}
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