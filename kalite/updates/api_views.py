"""
"""
import math

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseServerError

from updates.models import UpdateProgressLog
from utils.decorators import require_admin
from utils.general import isnumeric
from utils.internet import JsonResponse

@require_admin
def check_update_progress(request):
    """
    API endpoint for getting progress data on downloads.
    """
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
        raise Exception("Must specify process_id or process_name")

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
        "completed": process_log.completed or (process_log.end_time is not None),
        #"start_time": process_log.start_time,
    }