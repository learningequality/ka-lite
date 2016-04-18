"""
"""
import datetime
import dateutil.parser
import json
import os
import re
import math
from annoying.functions import get_object_or_None
from fle_utils.collections_local_copy import defaultdict

from django.conf import settings; logging = settings.LOG
from django.core.management import call_command
from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.utils.timezone import get_current_timezone, make_naive
from django.utils import translation
from django.utils.translation import ugettext as _

from .videos import delete_downloaded_files
from .models import UpdateProgressLog
from .views import get_installed_language_packs
from .download_track import VideoQueue
from fle_utils.chronograph.utils import force_job
from fle_utils.django_utils.command import call_command_async
from fle_utils.general import isnumeric, break_into_chunks, softload_json
from fle_utils.internet.decorators import api_handle_error_with_json
from fle_utils.internet.classes import JsonResponse, JsonResponseMessageError, JsonResponseMessageSuccess
from fle_utils.orderedset import OrderedSet
from kalite.i18n.base import lcode_to_ietf, delete_language, get_language_name
from kalite.shared.decorators.auth import require_admin
from kalite.topic_tools.settings import CHANNEL
from kalite.topic_tools.content_models import get_topic_update_nodes, get_download_youtube_ids, annotate_content_models_by_youtube_id


def process_log_from_request(handler):
    def wrapper_fn_pfr(request, *args, **kwargs):
        if request.GET.get("process_id"):
            # Get by ID--direct!
            if not isnumeric(request.GET["process_id"]):
                return JsonResponseMessageError(_("process_id is not numeric."), status=400)
            else:
                process_log = get_object_or_404(UpdateProgressLog, id=request.GET["process_id"])

        elif request.GET.get("process_name"):
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
    """
    API endpoint for launching the videodownload job.
    """
    force_job("videodownload", stop=True, locale=request.language)

    paths = OrderedSet(json.loads(request.body or "{}").get("paths", []))

    lang = json.loads(request.body or "{}").get("lang", "en")

    youtube_ids = get_download_youtube_ids(paths, language=lang, downloaded=False)

    queue = VideoQueue()

    queue.add_files(youtube_ids, language=lang)

    force_job("videodownload", _("Download Videos"), locale=lang)

    return JsonResponseMessageSuccess(_("Launched video download process successfully."))


@require_admin
@api_handle_error_with_json
def delete_videos(request):
    """
    API endpoint for deleting videos.
    """

    paths = OrderedSet(json.loads(request.body or "{}").get("paths", []))

    lang = json.loads(request.body or "{}").get("lang", "en")

    youtube_ids = get_download_youtube_ids(paths, language=lang, downloaded=True)

    num_deleted = 0

    for id in youtube_ids:
        # Delete the file on disk
        if delete_downloaded_files(id):
            num_deleted += 1

    annotate_content_models_by_youtube_id(youtube_ids=youtube_ids.keys(), language=lang)

    return JsonResponseMessageSuccess(_("Deleted %(num_videos)s video(s) successfully.") % {"num_videos": num_deleted})


@require_admin
@api_handle_error_with_json
def cancel_video_download(request):

    force_job("videodownload", stop=True)

    queue = VideoQueue()

    queue.clear()

    return JsonResponseMessageSuccess(_("Cancelled video download process successfully."))


@require_admin
@api_handle_error_with_json
def video_scan(request):

    lang = json.loads(request.body or "{}").get("lang", "en")

    force_job("videoscan", _("Scan for Videos"), language=lang)

    return JsonResponseMessageSuccess(_("Scanning for videos started."))


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

    call_command_async('retrievecontentpack', 'download', lang_code)

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


@require_admin
@api_handle_error_with_json
def get_update_topic_tree(request):

    parent = request.GET.get("parent")
    lang_code = request.GET.get("lang") or request.language      # Get annotations for the current language.

    return JsonResponse(get_topic_update_nodes(parent=parent, language=lang_code))


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
