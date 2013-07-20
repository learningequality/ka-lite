import json
import os
import readline
import SocketServer
import SimpleHTTPServer
import sys
import time
from khanacademy.test_oauth_client import TestOAuthClient
from oauth import OAuthToken

from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.utils.datastructures import MultiValueDictKeyError

import settings
from main.models import ExerciseLog, VideoLog
from main.topicdata import NODE_CACHE, ID2SLUG_MAP
from settings import LOG as logging
from utils.decorators import require_login, distributed_server_only, central_server_only



KHAN_SERVER_URL = "http://www.khanacademy.org"


@distributed_server_only
def start_auth(request):
    """
    Step 1 of oauth authentication: get the REQUEST_TOKEN
    """
    redirect_url = request.next or request.META.get("HTTP_REFERER", "") or reverse("homepage")
    callback_url = request.build_absolute_uri(reverse('update_all_callback')) + ("?next=%s" % redirect_url)
    client = TestOAuthClient(KHAN_SERVER_URL, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    return HttpResponseRedirect(client.start_fetch_request_token(callback_url))


@distributed_server_only
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


@distributed_server_only
def get_api_resource(request, resource_url):
    """
    Step 3 of the api process:
    Get the data.
    """
    central_server_url = "%s://%s/" % (settings.SECURESYNC_PROTOCOL, settings.CENTRAL_SERVER_HOST)
    client = TestOAuthClient(central_server_url, settings.KHAN_API_CONSUMER_KEY, settings.KHAN_API_CONSUMER_SECRET)
    start = time.time()
    response = client.access_resource("/api/khanload/" + resource_url, request.session["ACCESS_TOKEN"])
    end = time.time()

#    logging.debug(response)
    logging.debug("\nTime: %ss\n" % (end - start))

    return json.loads(response)


@distributed_server_only
@require_login
def update_all(request):
    """
    Update can't proceed without authentication.
    Start that process here.
    """
    # Will enter the callback, when it completes.
    return start_auth(request)


@distributed_server_only
@require_login
def update_all_callback(request):
    """
    Callback after authentication.

    Parses out the request token verification.
    Then finishes the request by getting an auth token.
    """

    access_token = finish_auth(request)

    logging.debug("Getting exercise data.")
    exercises = get_api_resource(request, reverse("user_exercises"))
    logging.debug("Got %d exercises" % len(exercises))

    logging.debug("Getting video data.")
    videos = get_api_resource(request, reverse("user_videos"))
    logging.debug("Got %d videos" % len(videos))

    user = request.session["facility_user"]

    # Save videos
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
            vl = VideoLog(
                user=user,
                youtube_id=youtube_id,
                total_seconds_watched=video['seconds_watched'],
                points=video['points'],
                complete=video['completed']
            )
            logging.debug("Saving video log for %s: %s" % (youtube_id, vl))
            vl.save()
        except KeyError:  # 
            logging.debug("Could not save video log for data with missing values: %s" % video)

    # Save exercises
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
            el = ExerciseLog(
                user=user,
                exercise_id=slug,
                streak_progress=min(100, 100*exercise['streak']/10),  # duplicates logic elsewhere
                attempts=exercise['total_done'],
                points=exercise['mastery_points'],
                complete=exercise['mastered'],
                attempts_before_completion=exercise['total_done'] if not exercise['practiced'] else None,  #can't figure this out if they practiced after mastery.
                completion_timestamp=exercise['proficient_date'] if exercise['mastered'] else None,
            )
            logging.debug("Saving exercise log for %s: %s" % (slug, el))
            el.save()
        except KeyError:
            logging.debug("Could not save exercise log for data with missing values: %s" % exercise)

    redirect_url = request.build_absolute_uri(request.GET.get("next", "") or reverse("homepage"))
    redirect_url_no_qs = redirect_url.split("?")[0]
    return HttpResponseRedirect(redirect_url_no_qs)


@central_server_only
def user_exercises(request):
    import pdb; pdb.set_trace()
    
def user_videos(request):
    import pdb; pdb.set_trace()