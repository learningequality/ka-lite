"""
"""
import datetime
import dateutil.parser
import json
import os
import re
import math
from annoying.functions import get_object_or_None
from collections_local_copy import defaultdict

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.utils.timezone import get_current_timezone, make_naive
from django.utils import translation
from django.utils.translation import ugettext as _

from . import delete_downloaded_files, get_local_video_size, get_remote_video_size
from .models import UpdateProgressLog, VideoFile
from .views import get_installed_language_packs
from fle_utils.chronograph.utils import force_job
from fle_utils.django_utils.command import call_command_async
from fle_utils.general import isnumeric, break_into_chunks, softload_json
from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError, JsonResponseMessageSuccess
from fle_utils.orderedset import OrderedSet
from kalite.i18n import get_youtube_id, get_video_language, lcode_to_ietf, delete_language, get_language_name
from kalite.shared.decorators.auth import require_admin
from kalite.topic_tools.settings import TOPICS_FILEPATHS, CHANNEL
from kalite.caching import initialize_content_caches


def divide_videos_by_language(youtube_ids):
    """Utility function for separating a list of youtube ids
    into a dictionary of lists, separated by video language
    (as determined by the current dubbed video map)
    """

    buckets_by_lang = defaultdict(lambda: [])
    for y_id in youtube_ids:
        buckets_by_lang[get_video_language(y_id)].append(y_id)
    return buckets_by_lang


def process_log_from_request(handler):
    def wrapper_fn_pfr(request, *args, **kwargs):
        if request.GET.get("process_id", None):
            # Get by ID--direct!
            if not isnumeric(request.GET["process_id"]):
                return JsonResponseMessageError(_("process_id is not numeric."), status=400)
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
                return JsonResponseMessageError(unicode(e), status=500)
        else:
            return JsonResponseMessageError(_("Must specify process_id or process_name"), status=400)

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

    return JsonResponseMessageSuccess(_("Cancelled update progress successfully."))


@require_admin
@api_handle_error_with_json
def start_video_download(request):
    force_job("videodownload", stop=True, locale=request.language)

    """
    API endpoint for launching the videodownload job.
    """
    youtube_ids = OrderedSet(simplejson.loads(request.body or "{}").get("youtube_ids", []))

    # One query per video (slow)
    video_files_to_create = [id for id in youtube_ids if not get_object_or_None(VideoFile, youtube_id=id)]

    # OK to do bulk_create; cache invalidation triggered via save download
    for lang_code, lang_youtube_ids in divide_videos_by_language(video_files_to_create).iteritems():
        VideoFile.objects.bulk_create([VideoFile(youtube_id=id, flagged_for_download=True, language=lang_code) for id in lang_youtube_ids])

    # OK to update all, since we're not setting all props above.
    # One query per chunk
    for chunk in break_into_chunks(youtube_ids):
        video_files_needing_model_update = VideoFile.objects.filter(download_in_progress=False, youtube_id__in=chunk).exclude(percent_complete=100)
        video_files_needing_model_update.update(percent_complete=0, cancel_download=False, flagged_for_download=True)

    force_job("videodownload", _("Download Videos"), locale=request.language)

    return JsonResponseMessageSuccess(_("Launched video download process successfully."))


@require_admin
@api_handle_error_with_json
def retry_video_download(request):
    """
    Clear any video still accidentally marked as in-progress, and restart the download job.
    """
    VideoFile.objects.filter(download_in_progress=True).update(download_in_progress=False, percent_complete=0)
    force_job("videodownload", _("Download Videos"), locale=request.language)

    return JsonResponseMessageSuccess(_("Launched video download process successfully."))


@require_admin
@api_handle_error_with_json
def delete_videos(request):
    """
    API endpoint for deleting videos.
    """
    youtube_ids = simplejson.loads(request.body or "{}").get("youtube_ids", [])
    num_deleted = 0

    for id in youtube_ids:
        # Delete the file on disk
        delete_downloaded_files(id)

        # Delete the file in the database
        found_videos = VideoFile.objects.filter(youtube_id=id)
        num_deleted += found_videos.count()
        found_videos.delete()

    initialize_content_caches(force=True)

    return JsonResponseMessageSuccess(_("Deleted %(num_videos)s video(s) successfully.") % {"num_videos": num_deleted})


@require_admin
@api_handle_error_with_json
def cancel_video_download(request):

    # clear all download in progress flags, to make sure new downloads will go through
    VideoFile.objects.all().update(download_in_progress=False)

    # unflag all video downloads
    VideoFile.objects.filter(flagged_for_download=True).update(cancel_download=True, flagged_for_download=False, download_in_progress=False)

    force_job("videodownload", stop=True, locale=request.language)

    return JsonResponseMessageSuccess(_("Cancelled video download process successfully."))


@api_handle_error_with_json
def installed_language_packs(request):
    return JsonResponse(get_installed_language_packs(force=True).values())


@require_admin
@api_handle_error_with_json
def start_languagepack_download(request):
    if not request.method == 'POST':
        raise Exception(_("Must call API endpoint with POST verb."))

    data = json.loads(request.raw_post_data)  # Django has some weird post processing into request.POST, so use .body
    lang_code = lcode_to_ietf(data['lang'])

    force_job('languagepackdownload', _("Language pack download"), lang_code=lang_code, locale=request.language)

    return JsonResponseMessageSuccess(_("Successfully started language pack download for %(lang_name)s.") % {"lang_name": get_language_name(lang_code)})


@require_admin
@api_handle_error_with_json
def delete_language_pack(request):
    """
    API endpoint for deleting language pack which fetches the language code (in delete_id) which has to be deleted.
    That particular language folders are deleted and that language gets removed.
    """
    lang_code = simplejson.loads(request.body or "{}").get("lang")
    delete_language(lang_code)

    return JsonResponse({"success": _("Successfully deleted language pack for %(lang_name)s.") % {"lang_name": get_language_name(lang_code)}})


def annotate_topic_tree(node, level=0, statusdict=None, remote_sizes=None, lang_code=None):
    # Not needed when on an api request (since translation.activate is already called),
    #   but just to do things right / in an encapsulated way...
    # Though to be honest, this isn't quite right; we should be DE-activating translation
    #   at the end.  But with so many function exit-points... just a nightmare.

    if not lang_code:
        lang_code = settings.LANGUAGE_CODE

    if level == 0:
        translation.activate(lang_code)

    if not statusdict:
        statusdict = {}

    if node["kind"] == "Topic":
        if "Video" not in node["contains"]:
            return None

        children = []
        unstarted = True
        complete = True

        for child_node in node["children"]:
            child = annotate_topic_tree(child_node, level=level + 1, statusdict=statusdict, lang_code=lang_code)
            if not child:
                continue
            elif child["extraClasses"] == "unstarted":
                complete = False
            elif child["extraClasses"] == "partial":
                complete = False
                unstarted = False
            elif child["extraClasses"] == "complete":
                unstarted = False
            children.append(child)

        if not children:
            # All children were eliminated; so eliminate self.
            return None

        return {
            "title": _(node["title"]),
            "tooltip": re.sub(r'<[^>]*?>', '', _(node.get("description")) or ""),
            "folder": True,
            "key": node["id"],
            "children": children,
            "extraClasses": complete and "complete" or unstarted and "unstarted" or "partial",
            "expanded": level < 1,
        }

    elif node["kind"] == "Video":
        video_id = node.get("youtube_id", node.get("id"))
        youtube_id = get_youtube_id(video_id, lang_code=lang_code)

        if not youtube_id:
            # This video doesn't exist in this language, so remove from the topic tree.
            return None

        # statusdict contains an item for each video registered in the database
        # will be {} (empty dict) if there are no videos downloaded yet
        percent = statusdict.get(youtube_id, 0)
        vid_size = None
        status = None

        if not percent:
            status = "unstarted"
            vid_size = get_remote_video_size(youtube_id) / float(2 ** 20)  # express in MB
        elif percent == 100:
            status = "complete"
            vid_size = get_local_video_size(youtube_id, 0) / float(2 ** 20)  # express in MB
        else:
            status = "partial"

        return {
            "title": _(node["title"]),
            "tooltip": re.sub(r'<[^>]*?>', '', _(node.get("description")) or ""),
            "key": youtube_id,
            "extraClasses": status,
            "size": vid_size,
        }

    return None


@require_admin
@api_handle_error_with_json
def get_annotated_topic_tree(request, lang_code=None):
    call_command("videoscan")  # Could potentially be very slow, blocking request... but at least it's via an API request!

    lang_code = lang_code or request.language      # Get annotations for the current language.
    statusdict = dict(VideoFile.objects.values_list("youtube_id", "percent_complete"))

    return JsonResponse(annotate_topic_tree(softload_json(TOPICS_FILEPATHS.get(CHANNEL), logger=logging.debug, raises=False), statusdict=statusdict, lang_code=lang_code))


"""
Software updates
"""


@require_admin
def start_update_kalite(request):
    try:
        data = json.loads(request.body)
        mechanism = data['mechanism']
    except KeyError:
        raise KeyError(_("You did not select a valid choice for an update mechanism."))

    # Clear any preexisting logs
    if UpdateProgressLog.objects.count():
        UpdateProgressLog.objects.all().delete()

    call_command_async('update', mechanism, old_server_pid=os.getpid(), in_proc=True)

    return JsonResponseMessageSuccess(_("Launched software update process successfully."))
