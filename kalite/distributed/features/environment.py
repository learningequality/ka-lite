"""
environment.py specific to the this app
"""
from kalite.testing.base_environment import before_all, after_all, before_feature, after_feature, before_scenario as base_before_scenario, after_scenario

import random
import datetime

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.topic_tools import get_exercise_cache, get_content_cache


def before_scenario(context, scenario):
    base_before_scenario(context, scenario)

    if "with_progress" in context.tags:
        user = FacilityUser.objects.get(username=context.user, facility=getattr(context, "facility", None))
        exercises = random.sample(get_exercise_cache().keys(), 2)
        for exercise in exercises:
            log = ExerciseLog(
                exercise_id=exercise,
                user=user,
                streak_progress=50,
                attempts=15,
                latest_activity_timestamp=datetime.datetime.now()
                )
            log.save()
        context.exercises = exercises

        videos = random.sample(get_content_cache().keys(), 2)

        for video in videos:
            log = VideoLog(
                youtube_id=video,
                video_id=video,
                user=user,
                total_seconds_watched=100,
                points=600,
                latest_activity_timestamp=datetime.datetime.now()
                )
            log.save()
        context.videos = videos