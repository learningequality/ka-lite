import datetime
import json
import oauth
import os
import readline
import requests
import SocketServer
import SimpleHTTPServer
import sys
import time
from khanacademy.test_oauth_client import TestOAuthClient
from oauth import OAuthToken

from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt

import settings
from main.models import ExerciseLog, VideoLog
from main.topicdata import NODE_CACHE, ID2SLUG_MAP
from settings import LOG as logging
from securesync.models import FacilityUser
from utils.decorators import require_login, distributed_server_only, central_server_only
from utils.internet import JsonResponse


KHAN_SERVER_URL = "http://www.khanacademy.org"
CENTRAL_SERVER_URL = "%s://%s" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST)


def requests_response_to_django_response(requests_response):
    django_response = HttpResponse(requests_response.content, status=requests_response.status_code)
    for key, val in requests_response.headers.items(): 
        django_response[key] = val
    print str(django_response)
    return django_response


@central_server_only
def start_auth(request):
    """
    Step 1 of oauth authentication: get the REQUEST_TOKEN
    """

    # Redirect to KA, for auth.  They will return to central, and we'll be able to continue
    #   using data from the session
    central_callback_url = request.build_absolute_uri(reverse('update_all_central_callback'))
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    return HttpResponseRedirect(client.start_fetch_request_token(central_callback_url))


@central_server_only
def finish_auth(request):
    """
    Step 2 of the oauth authentication: use the REQUEST_TOKEN to get an ACCESS_TOKEN
    """
    params = request.GET
    try:
        request.session["REQUEST_TOKEN"] = OAuthToken(params['oauth_token'], params['oauth_token_secret'])
        request.session["REQUEST_TOKEN"].set_verifier(params['oauth_verifier'])
    except MultiValueDictKeyError as e:
        # we just want to generate a 500 anyway; 
        #   nothing we could do here except give a slightly more meaningful error
        raise e

    logging.debug("Getting access token.")
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    request.session["ACCESS_TOKEN"] = client.fetch_access_token(request.session["REQUEST_TOKEN"])
    if not request.session["ACCESS_TOKEN"]:
        raise Exception("Did not get access token.")

    return request.session["ACCESS_TOKEN"]


@central_server_only
def get_api_resource(request, resource_url):
    """
    Step 3 of the api process:
    Get the data.
    """
    logging.info("Getting data from khan academy (%s)." % resource_url)
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    start = time.time()
    response = client.access_resource(resource_url, request.session["ACCESS_TOKEN"])
    end = time.time()

    logging.debug("API (%s) time: %s" % (resource_url, end - start))
    data = json.loads(response)
    logging.info("Got %d items from khan academy (%s)." % (len(data), resource_url))

    return data


@central_server_only
def update_all_central(request):
    """
    Update can't proceed without authentication.
    Start that process here.
    """

    # Store information in a session
    request.session["distributed_user_id"] = request.GET["user_id"]
    # TODO(bcipolli): remove total HACK to get playground demo to work.
    request.session["distributed_callback_url"] = request.GET["callback"].replace("playground.learningequality.org","10.28.237.39")
    request.session["distributed_redirect_url"] = request.next or request.META.get("HTTP_REFERER", "") or "/"
    request.session["distributed_csrf_token"] = request._cookies["csrftoken"]

    if True or not "ACCESS_TOKEN" in request.session:
        # Will enter the callback, when it completes.
        logging.debug("starting new authorization handshake")
        return start_auth(request)
    else:
        logging.debug("using cached authorization handshake")
        return update_all_central_callback(request)

def convert_ka_date(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")

@central_server_only
def update_all_central_callback(request):
    """
    Callback after authentication.

    Parses out the request token verification.
    Then finishes the request by getting an auth token.
    """
    if not "ACCESS_TOKEN" in request.session:
        finish_auth(request)
    
    exercises = get_api_resource(request, "/api/v1/user/exercises")
    videos = get_api_resource(request, "/api/v1/user/videos")

    # Save videos
    video_logs = []
    for video in videos:
        youtube_id =video.get('video', {}).get('youtube_id', "")

        # Only save videos with progress
        if not video.get('seconds_watched', None):
            continue

        # Only save video logs for videos that we recognize.
        if youtube_id not in ID2SLUG_MAP:
            logging.debug("Skipping unknown video %s" % youtube_id)
            continue

        try:
            video_logs.append({
                "youtube_id": youtube_id,
                "total_seconds_watched": video['seconds_watched'],
                "points": video['points'],
                "complete": video['completed'],
                "completion_timestamp": convert_ka_date(video['last_watched']) if video['completed'] else None,
            })
            logging.debug("Got video log for %s: %s" % (youtube_id, video_logs[-1]))
        except KeyError:  # 
            logging.debug("Could not save video log for data with missing values: %s" % video)

    # Save exercises
    exercise_logs = []
    for exercise in exercises:
        # Only save exercises that have any progress.
        if not exercise.get('last_done', None):
            continue

        # Only save video logs for videos that we recognize.
        slug = exercise.get('exercise', "")
        if slug not in NODE_CACHE['Exercise']:
            logging.debug("Skipping unknown video %s" % slug)
            continue

        try:
            completed = exercise['streak'] >= 10
            exercise_logs.append({
                "exercise_id": slug,
                "streak_progress": min(100, 100*exercise['streak']/10),  # duplicates logic elsewhere
                "attempts": exercise['total_done'],
                "points": exercise['total_correct'] * 12,
                "complete": completed,
                "attempts_before_completion": exercise['total_done'] if not exercise['practiced'] else None,  #can't figure this out if they practiced after mastery.
                "completion_timestamp": convert_ka_date(exercise['proficient_date']) if completed else None,
            })
            logging.debug("Got exercise log for %s: %s" % (slug, exercise_logs[-1]))
        except KeyError:
            logging.debug("Could not save exercise log for data with missing values: %s" % exercise)

    # TODO(bcipolli): validate response
    dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
    logging.debug("POST'ing to %s" % request.session["distributed_callback_url"])
    response = requests.post(
        request.session["distributed_callback_url"],
        cookies={ "csrftoken": request.session["distributed_csrf_token"] },
        data = {
            "csrfmiddlewaretoken": request.session["distributed_csrf_token"],
            "video_logs": json.dumps(video_logs, default=dthandler),
            "exercise_logs": json.dumps(exercise_logs, default=dthandler),
            "user_id": request.session["distributed_user_id"],
        }
    )
    if response.status_code != 200:
        raise Exception("Status code == %d:\n%s" % (response.status_code, response.content))
    logging.debug("Response: %s" % response.content)

    return HttpResponseRedirect(request.session["distributed_redirect_url"])


@distributed_server_only
@require_login
def update_all_distributed(request):
    logging.debug("Getting data.")

    params = {
        "callback": request.build_absolute_uri(reverse("update_all_distributed_callback")),
        "user_id": request.session["facility_user"].id,
    }

    query_string = "&".join(["%s=%s" % (k,oauth.escape(v)) for k,v in params.items()])
    central_url = CENTRAL_SERVER_URL + reverse("update_all_central") + "?" + query_string

    return HttpResponseRedirect(central_url)


@csrf_exempt
@distributed_server_only
def update_all_distributed_callback(request):
    """
    """

    if request.method != "POST":
        raise PermissionDenied("Only POST allowed to this URL endpoint.")

    videos = json.loads(request.POST["video_logs"])
    exercises = json.loads(request.POST["exercise_logs"])
    user = FacilityUser.objects.get(id=request.POST["user_id"])

    # Save videos
    n_videos_uploaded = 0
    for video in videos:
        youtube_id =video['youtube_id']

        # Only save video logs for videos that we recognize.
        if youtube_id not in ID2SLUG_MAP:
            logging.debug("Skipping unknown video %s" % youtube_id)
            continue

        try:
            vl = VideoLog(user=user, **video)
            logging.debug("Saving video log for %s: %s" % (youtube_id, vl))
            vl.save()
            n_videos_uploaded += 1
        except KeyError:  # 
            logging.debug("Could not save video log for data with missing values: %s" % video)

    # Save exercises
    n_exercises_uploaded = 0
    for exercise in exercises:
        # Only save video logs for videos that we recognize.
        if exercise['exercise_id'] not in NODE_CACHE['Exercise']:
            logging.debug("Skipping unknown video %s" % exercise['exercise_id'])
            continue

        try:
            el = ExerciseLog(user=user, **exercise)
            logging.debug("Saving exercise log for %s: %s" % (exercise['exercise_id'], el))
            el.save()
            n_exercises_uploaded += 1
        except KeyError:
            logging.debug("Could not save exercise log for data with missing values: %s" % exercise)

    return HttpResponse("Uploaded %d exercises and %d videos" % (n_exercises_uploaded, n_videos_uploaded))
