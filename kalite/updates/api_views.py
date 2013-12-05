"""
"""
import datetime
import dateutil.parser
import json
import re
import math
from annoying.functions import get_object_or_None

from django.core.management import call_command
from django.db.models import Q
from django.http import HttpResponse, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.utils import simplejson
from django.utils.timezone import get_current_timezone, make_naive
from django.utils.translation import ugettext as _

import settings
from .models import UpdateProgressLog, VideoFile
from .views import get_installed_language_packs
from main import topicdata
from shared.decorators import require_admin
from shared.jobs import force_job
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
                return JsonResponse({"error": _("process_id is not numeric.")}, status=500);
            else:
                process_log = get_object_or_404(UpdateProgressLog, id=request.GET["process_id"])

        elif request.GET.get("process_name", None):
            process_name = request.GET["process_name"]
            if "start_time" not in request.GET:
                start_time = datetime.datetime.now()
            else:
                start_time = make_naive(dateutil.parser.parse(request.GET["start_time"]), get_current_timezone())

            try:
                # Get the latest one of a particular name--indirect
                process_log = UpdateProgressLog.get_active_log(process_name=process_name, create_new=False)

                if not process_log:
                    # Still waiting; get the very latest, at least.
                    logs = UpdateProgressLog.objects \
                        .filter(process_name=process_name, completed=True, end_time__gt=start_time) \
                        .order_by("-end_time")
                    if logs:
                        process_log = logs[0]
            except Exception as e:
                # The process finished before we started checking, or it's been deleted.
                #   Best to complete silently, but for debugging purposes, will make noise for now.
                return JsonResponse({"error": str(e)}, status=500);
        else:
            return JsonResponse({"error": _("Must specify process_id or process_name")})

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

    if not process_log or not process_log.total_stages:
        return {}
    else:
        return {
            "process_id": process_log.id,
            "process_name": process_log.process_name,
            "process_percent": process_log.process_percent,
            "stage_name": process_log.stage_name,
            "stage_percent": process_log.stage_percent,
            "stage_status": process_log.stage_status,
            "cur_stage_num": 1 + int(math.floor(process_log.total_stages * process_log.process_percent)),
            "total_stages": process_log.total_stages,
            "notes": process_log.notes,
            "completed": process_log.completed or (process_log.end_time is not None),
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

    # One query per video (slow)
    video_files_to_create = [id for id in youtube_ids if not get_object_or_None(VideoFile, youtube_id=id)]
    video_files_to_update = youtube_ids - OrderedSet(video_files_to_create)

    # OK to do bulk_create; cache invalidation triggered via save download
    VideoFile.objects.bulk_create([VideoFile(youtube_id=id, flagged_for_download=True) for id in video_files_to_create])

    # One query per chunk
    for chunk in break_into_chunks(youtube_ids):
        video_files_needing_model_update = VideoFile.objects.filter(download_in_progress=False, youtube_id__in=chunk).exclude(percent_complete=100)
        video_files_needing_model_update.update(percent_complete=0, cancel_download=False, flagged_for_download=True)

    force_job("videodownload", _("Download Videos"))
    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def retry_video_download(request):
    """
    Clear any video still accidentally marked as in-progress, and restart the download job.
    """
    VideoFile.objects.filter(download_in_progress=True).update(download_in_progress=False, percent_complete=0)
    force_job("videodownload", _("Download Videos"))
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
        VideoFile.objects.filter(youtube_id=id).delete()

    return JsonResponse({})


@require_admin
@api_handle_error_with_json
def cancel_video_download(request):

    # clear all download in progress flags, to make sure new downloads will go through
    VideoFile.objects.all().update(download_in_progress=False)

    # unflag all video downloads
    VideoFile.objects.filter(flagged_for_download=True).update(cancel_download=True, flagged_for_download=False, download_in_progress=False)

    force_job("videodownload", stop=True)

    return JsonResponse({})

@api_handle_error_with_json
def installed_language_packs(request):
    installed = list(get_installed_language_packs())
    is_en_in_language_packs = filter(lambda l: l['code'] == 'en', installed)
    if not is_en_in_language_packs:
        en = {'name': 'English',
              'code': 'en',
              'subtitle_count': 0,
              'percent_translated': 100,  # Our software is written in english
              'language_pack_version': 0,  # so that it can always be upgraded if there's an en language pack
        }
        installed.insert(0, en)         # prepend so that it's always at the top of the list of languages
    return JsonResponse(installed)

@require_admin
@api_handle_error_with_json
def start_languagepack_download(request):
    if request.POST:
        data = json.loads(request.raw_post_data) # Django has some weird post processing into request.POST, so use raw_post_data
        call_command_async(
            'languagepackdownload',
            manage_py_dir=settings.PROJECT_PATH,
            language=data['lang']) # TODO: migrate to force_job once it can accept command_args
        return JsonResponse({'success': True})


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
            "title": _(node["title"]),
            "tooltip": re.sub(r'<[^>]*?>', '', node["description"] or ""),
            "isFolder": True,
            "key": node["id"],
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
def cancel_update_kalite(request):
    return JsonResponse({})
