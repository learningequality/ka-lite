"""
"""
import json
import re
import math
from annoying.functions import get_object_or_None

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseServerError
from django.utils import simplejson
from django.core.management import call_command
from django.db.models import Q

import settings
from .models import UpdateProgressLog
from main.models import VideoFile
from main import topicdata
from shared.caching import invalidate_all_pages_related_to_video
from shared.decorators import require_admin
from shared.jobs import force_job, job_status
from shared.videos import delete_downloaded_files
from utils.django_utils import call_command_async
from utils.general import isnumeric, break_into_chunks
from utils.internet import api_handle_error_with_json, JsonResponse
from utils.orderedset import OrderedSet


def process_log_from_request(handler):
    def wrapper_fn_pfr(request, *args, **kwargs):
        if request.GET.get("process_id", None):
            # Get by ID--direct!
            if not isnumeric(request.GET["process_id"]):
                return JsonResponse({"error": "process_id is not numeric."}, status=500);
            else:
                process_log = get_object_or_404(UpdateProgressLog, id=request.GET["process_id"])

        elif request.GET.get("process_name", None):
            # Get the latest one of a particular name--indirect
            try:
                process_log = UpdateProgressLog.get_active_log(process_name=request.GET["process_name"], create_new=False)
            except Exception as e:
                # The process finished before we started checking, or it's been deleted.
                #   Best to complete silently, but for debugging purposes, will make noise for now.
                return JsonResponse({"error": str(e)}, status=500);
        else:
            return JsonResponse({"error": "Must specify process_id or process_name"})

        return handler(request, process_log, *args, **kwargs)
    return wrapper_fn_pfr


@require_admin
@api_handle_error_with_json
@process_log_from_request
def check_update_progress(request, process_log):
    """
    API endpoint for getting progress data on downloads.
    """
    return JsonResponse(_process_log_to_dict(process_log))


def _process_log_to_dict(process_log):
    """
    Utility function to convert a process log to a dict
    """
    
    return {} if not process_log else {
        "process_id": process_log.id,
        "process_name": process_log.process_name,
        "process_percent": process_log.process_percent,
        "stage_name": process_log.stage_name,
        "stage_percent": process_log.stage_percent,
        "cur_stage_num": 1 + int(math.floor(process_log.total_stages * process_log.process_percent)),
        "total_stages": process_log.total_stages,
        "notes": process_log.notes,
        "completed": process_log.completed or (process_log.end_time is not None),
        #"start_time": process_log.start_time,
    }

@require_admin
@api_handle_error_with_json
@process_log_from_request
def cancel_update_progress(request, process_log):
    """
    API endpoint for getting progress data on downloads.
    """
    process_log.cancel_requested = True
    process_log.save()

    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def start_video_download(request):
    """
    API endpoint for launching the videodownload job.
    """
    youtube_ids = OrderedSet(simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", []))

    video_files_to_create = [id for id in youtube_ids if not get_object_or_None(VideoFile, youtube_id=id)]
    video_files_to_update = youtube_ids - OrderedSet(video_files_to_create)

    VideoFile.objects.bulk_create([VideoFile(youtube_id=id, flagged_for_download=True) for id in video_files_to_create])

    for chunk in break_into_chunks(youtube_ids):
        video_files_needing_model_update = VideoFile.objects.filter(download_in_progress=False, youtube_id__in=chunk).exclude(percent_complete=100)
        video_files_needing_model_update.update(percent_complete=0, cancel_download=False, flagged_for_download=True)

    force_job("videodownload", "Download Videos")
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def check_video_download(request):
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    percentages = {}
    percentages["downloading"] = job_status("videodownload")
    for id in youtube_ids:
        videofile = get_object_or_None(VideoFile, youtube_id=id) or VideoFile(youtube_id=id)
        percentages[id] = videofile.percent_complete
    return JsonResponse(percentages)


@require_admin
@api_handle_error_with_json
def retry_video_download(request):
    """Clear any video still accidentally marked as in-progress, and restart the download job.
    """
    VideoFile.objects.filter(download_in_progress=True).update(download_in_progress=False, percent_complete=0)
    force_job("videodownload", "Download Videos")
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def delete_videos(request):
    """
    API endpoint for deleting videos.
    """
    youtube_ids = simplejson.loads(request.raw_post_data or "{}").get("youtube_ids", [])
    for id in youtube_ids:
        # Delete the file on disk
        delete_downloaded_files(id)

        # Delete the file in the database
        videofile = get_object_or_None(VideoFile, youtube_id=id)
        if videofile:
            videofile.cancel_download = True
            videofile.flagged_for_download = False
            videofile.flagged_for_subtitle_download = False
            videofile.save()

        # Refresh the cache
        invalidate_all_pages_related_to_video(video_id=id)

    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def retry_video_download(request):
    """Clear any video still accidentally marked as in-progress, and restart the download job.
    """
    VideoFile.objects.filter(download_in_progress=True).update(download_in_progress=False, percent_complete=0)
    force_job("videodownload", "Download Videos")
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def cancel_video_download(request):

    # clear all download in progress flags, to make sure new downloads will go through
    VideoFile.objects.all().update(download_in_progress=False)

    # unflag all video downloads
    VideoFile.objects.filter(flagged_for_download=True).update(cancel_download=True, flagged_for_download=False)

    force_job("videodownload", stop=True)
    log = UpdateProgressLog.get_active_log(process_name="videodownload", create_new=False)
    if log:
        log.cancel_progress()

    return JsonResponse({})



def annotate_topic_tree(node, level=0, statusdict=None):
    if not statusdict:
        statusdict = {}
    if node["kind"] == "Topic":
        if "Video" not in node["contains"]:
            return None
        children = []
        unstarted = True
        complete = True
        for child_node in node["children"]:
            child = annotate_topic_tree(child_node, level=level+1, statusdict=statusdict)
            if child:
                if child["addClass"] == "unstarted":
                    complete = False
                if child["addClass"] == "partial":
                    complete = False
                    unstarted = False
                if child["addClass"] == "complete":
                    unstarted = False
                children.append(child)
        return {
            "title": node["title"],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "isFolder": True,
            "key": node["slug"],
            "children": children,
            "addClass": complete and "complete" or unstarted and "unstarted" or "partial",
            "expand": level < 1,
        }
    if node["kind"] == "Video":
        #statusdict contains an item for each video registered in the database
        # will be {} (empty dict) if there are no videos downloaded yet
        percent = statusdict.get(node["youtube_id"], 0)
        if not percent:
            status = "unstarted"
        elif percent == 100:
            status = "complete"
        else:
            status = "partial"
        return {
            "title": node["title"],
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "key": node["youtube_id"],
            "addClass": status,
        }
    return None

@require_admin
@api_handle_error_with_json
def get_annotated_topic_tree(request):
    statusdict = dict(VideoFile.objects.values_list("youtube_id", "percent_complete"))
    return JsonResponse(annotate_topic_tree(topicdata.TOPICS, statusdict=statusdict))


"""
Subtitles
"""

@require_admin
@api_handle_error_with_json
def start_subtitle_download(request):
    """Totally broken, until @dylanjbarth takes this on."""
    update_set = simplejson.loads(request.raw_post_data or "{}").get("update_set", "existing")
    language = simplejson.loads(request.raw_post_data or "{}").get("language", "")
    language_list = []#topicdata.LANGUAGE_LIST
    language_lookup = []#topicdata.LANGUAGE_LOOKUP

    # Reset the language
    current_language = Settings.get("subtitle_language")
    if language in language_list:
        Settings.set("subtitle_language", language)
    else:
        return JsonResponse({"error": "This language is not currently supported - please update the language list"}, status=500)

    language_name = language_lookup.get(language)
    # Get the json file with all srts
    request_url = "http://%s/static/data/subtitles/languages/%s_available_srts.json" % (settings.CENTRAL_SERVER_HOST, language)
    try:
        r = requests.get(request_url)
        r.raise_for_status() # will return none if 200, otherwise will raise HTTP error
        available_srts = set((r.json)["srt_files"])
    except ConnectionError:
        return JsonResponse({"error": "The central server is currently offline."}, status=500)
    except HTTPError:
        return JsonResponse({"error": "No subtitles available on central server for %s (language code: %s); aborting." % (language_name, language)}, status=500)

    if update_set == "existing":
        videofiles = VideoFile.objects.filter(Q(percent_complete=100) | Q(flagged_for_download=True), subtitles_downloaded=False, youtube_id__in=available_srts)
    else:
        videofiles = VideoFile.objects.filter(Q(percent_complete=100) | Q(flagged_for_download=True), youtube_id__in=available_srts)

    if not videofiles:
        return JsonResponse({"info": "There aren't any subtitles available in %s (language code: %s) for your current videos." % (language_name, language)}, status=200)
    else:   
        for videofile in videofiles:
            videofile.cancel_download = False
            if videofile.subtitle_download_in_progress:
                continue
            videofile.flagged_for_subtitle_download = True
            if update_set == "all":
                videofile.subtitles_downloaded = False
            videofile.save()
        
    force_job("subtitledownload", "Download Subtitles")
    return JsonResponse({})

@require_admin
@api_handle_error_with_json
def check_subtitle_download(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True)
    return JsonResponse(videofiles.count())

@require_admin
@api_handle_error_with_json
def get_subtitle_download_list(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True).values("youtube_id")
    video_ids = [video["youtube_id"] for video in videofiles]
    return JsonResponse(video_ids)


@require_admin
@api_handle_error_with_json
def cancel_subtitle_download(request):
    # unflag all subtitle downloads
    VideoFile.objects.filter(flagged_for_subtitle_download=True).update(cancel_download=True, flagged_for_subtitle_download=False)

    force_job("subtitledownload", stop=True)
    return JsonResponse({})


"""
Software updates
"""

@require_admin
def start_update_kalite(request):
    data = json.loads(request.raw_post_data)

    if request.META.get("CONTENT_TYPE", "") == "application/json" and "url" in data:
        # Got a download url
        call_command_async("update", url=data["url"], manage_py_dir=settings.PROJECT_PATH)

    elif request.META.get("CONTENT_TYPE", "") == "application/zip":
        # Streamed a file; save and call
        fp, tempfile = tempfile.mkstmp()
        with fp:
            write(request.content)
        call_command_async("update", zip_file=tempfile, manage_py_dir=settings.PROJECT_PATH)

    return JsonResponse({})

@require_admin
def check_update_kalite(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True)
    return JsonResponse(videofiles.count())

@require_admin
def get_update_kalite_list(request):
    videofiles = VideoFile.objects.filter(flagged_for_subtitle_download=True).values("youtube_id")
    video_ids = [video["youtube_id"] for video in videofiles]
    return JsonResponse(video_ids)

@require_admin
def cancel_update_kalite(request):
    # unflag all subtitle downloads
    VideoFile.objects.filter(flagged_for_subtitle_download=True).update(cancel_download=True, flagged_for_subtitle_download=False)

    force_job("subtitledownload", stop=True)
    return JsonResponse({})
