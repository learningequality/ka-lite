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

from main.models import ExerciseLog, VideoLog
from main.topicdata import NODE_CACHE, ID2SLUG_MAP
from settings import LOG as logging
from utils.decorators import require_login


# This is a quick, gross little interactive script for testing our OAuth API.

CONSUMER_KEY = "vrwxbbWvh7PwTkzk"
CONSUMER_SECRET = "xLxMgDKEj5EMdThf"
SERVER_URL = "http://www.khanacademy.org"


REQUEST_TOKEN = None
ACCESS_TOKEN = None


def get_request_token(request):
    redirect_url = request.META.get("HTTP_REFERER", "") or reverse("homepage")
    callback_url = request.build_absolute_uri(reverse('update_all_callback')) + ("?next=%s" % redirect_url)
    client = TestOAuthClient(SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
    return HttpResponseRedirect(client.start_fetch_request_token(callback_url))


def get_access_token(request):
    global ACCESS_TOKEN

    client = TestOAuthClient(SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
    ACCESS_TOKEN = client.fetch_access_token(REQUEST_TOKEN)


def get_api_resource(resource_url):
    client = TestOAuthClient(SERVER_URL, CONSUMER_KEY, CONSUMER_SECRET)
    start = time.time()
    response = client.access_resource(resource_url, ACCESS_TOKEN)
    end = time.time()

#    logging.debug(response)
    logging.debug("\nTime: %ss\n" % (end - start))

    return json.loads(response)


@require_login
def update_all(request):
    # Will enter the callback, when it completes.
    return get_request_token(request)

@require_login
def update_all_callback(request):
    """
    Parses out the request token verification.
    Then finishes the request by getting an auth token.
    """
    global REQUEST_TOKEN

    params = request.GET
    REQUEST_TOKEN = OAuthToken(params['oauth_token'], params['oauth_token_secret'])
    REQUEST_TOKEN.set_verifier(params['oauth_verifier'])


    logging.debug("Getting access token.")
    get_access_token(request)
    if not ACCESS_TOKEN:
        logging.debug("Did not get access token.")
    
    else:
        logging.debug("Getting exercise data.")
        exercises = get_api_resource("/api/v1/user/exercises")
        logging.debug("Got %d exercises" % len(exercises))

        logging.debug("Getting video data.")
        videos = get_api_resource("/api/v1/user/videos")
        logging.debug("Got %d videos" % len(videos))

        user = request.session["facility_user"]

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
