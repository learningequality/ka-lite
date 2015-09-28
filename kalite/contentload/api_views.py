"""
This file implements both the central and distributed server sides of
a handshake to download KA data.

Why does the central server have to be involved?
  - because we have exactly one API Key for KA, and we don't want to share it
  with distributed server accounts.
  - because we don't trust KA to keep their API static; by putting the central
  server in the middle, we can easily update, and distributed servers don't break.

Here's how it works:
* On the distributed server, there is a button on the facility user's "account" page with a button"Download data from KA".
* That button has a link to a distributed server url.  The user clicks it.
* That distributed server view sets up a proper URL/request to the central server, then redirects that central server URL.
* The central server tries to authenticate to KA (forwarding users to KA), with a call-back URL when that succeeds.
* The user authenticates with KA, and KA oauth is returned to the central server.
* The central server then uses the KA API to get the user data, interpret it, massage it, and compute (our) relevant quantities.
* The central server then uses a distributed server call-back URL to POST the downloaded user data.
* The distributed server gets that data, loads it, saves it, and then redirects the user--to their account page.
* The account page shows again, this time including the imported KA data
"""
import json

from django.conf import settings; logging = settings.LOG
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

from fle_utils.internet.classes import JsonResponseMessageError, JsonResponseMessageSuccess
from fle_utils.internet.functions import set_query_params
from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.shared.decorators.auth import require_login
from kalite.topic_tools.content_models import get_content_items

CENTRAL_SERVER_URL = "%s://%s" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST)
CENTRAL_UPDATE_ALL_PATH = "/api/contentload/update/central/"


@require_login
def update_all_distributed(request):
    """
    """
    logging.debug("Getting Khan Academy data.")

    return HttpResponseRedirect(set_query_params(CENTRAL_SERVER_URL + CENTRAL_UPDATE_ALL_PATH, {
        "callback": request.build_absolute_uri(reverse("update_all_distributed_callback")),
        "user_id": request.session["facility_user"].id,
    }))


@csrf_exempt
def update_all_distributed_callback(request):
    """
    """

    if request.method != "POST":
        raise PermissionDenied("Only POST allowed to this URL endpoint.")

    videos = json.loads(request.POST["video_logs"])
    exercises = json.loads(request.POST["exercise_logs"])
    user = FacilityUser.objects.get(id=request.POST["user_id"])
    node_ids = [node.get("id") for node in get_content_items()]
    # Save videos
    n_videos_uploaded = 0
    for video in videos:
        video_id = video['video_id']
        youtube_id = video['youtube_id']

        # Only save video logs for videos that we recognize.
        if video_id not in node_ids:
            logging.warn("Skipping unknown video %s" % video_id)
            continue

        try:
            (vl, _) = VideoLog.get_or_initialize(user=user, video_id=video_id)  # has to be that video_id, could be any youtube_id
            for key,val in video.iteritems():
                setattr(vl, key, val)
            logging.debug("Saving video log for %s: %s" % (video_id, vl))
            vl.save()
            n_videos_uploaded += 1
        except KeyError:  #
            logging.error("Could not save video log for data with missing values: %s" % video)
        except Exception as e:
            error_message = _("Unexpected error importing videos: %(err_msg)s") % {"err_msg": e}
            return JsonResponseMessageError(error_message, status=500)

    # Save exercises
    n_exercises_uploaded = 0
    for exercise in exercises:
        # Only save video logs for videos that we recognize.
        if exercise['exercise_id'] not in node_ids:
            logging.warn("Skipping unknown video %s" % exercise['exercise_id'])
            continue

        try:
            (el, _) = ExerciseLog.get_or_initialize(user=user, exercise_id=exercise["exercise_id"])
            for key,val in exercise.iteritems():
                setattr(el, key, val)
            logging.debug("Saving exercise log for %s: %s" % (exercise['exercise_id'], el))
            el.save()
            n_exercises_uploaded += 1
        except KeyError:
            logging.error("Could not save exercise log for data with missing values: %s" % exercise)
        except Exception as e:
            error_message = _("Unexpected error importing exercises: %(err_msg)s") % {"err_msg": e}
            return JsonResponseMessageError(error_message, status=500)

    return JsonResponseMessageSuccess(_("Uploaded %(num_exercises)d exercises and %(num_videos)d videos") % {
        "num_exercises": n_exercises_uploaded,
        "num_videos": n_videos_uploaded,
    })
