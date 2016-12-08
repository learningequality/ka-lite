"""
environment.py specific to the this app
"""

# These are auto-discovered by Behave? So nevermind that they're unused?
from kalite.testing.base_environment import before_all, after_all, before_feature, after_feature, before_scenario as base_before_scenario, after_scenario

import random
import datetime

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog


def before_scenario(context, scenario):
    base_before_scenario(context, scenario)

    if "with_progress" in context.tags:
        user = FacilityUser.objects.get(username=context.user, facility=getattr(context, "facility", None))
        exercises = random.sample(context.content_exercises, 2)
        for exercise in exercises:
            log = ExerciseLog(
                exercise_id=exercise.id,
                user=user,
                streak_progress=50,
                attempts=15,
                latest_activity_timestamp=datetime.datetime.now()
                )
            log.save()
        context.content_exercises = exercises

        # Mark 2 videos watched
        videos = random.sample(context.content_videos, 2)

        for video in videos:
            log = VideoLog(
                youtube_id=video.id,
                video_id=video.id,
                user=user,
                total_seconds_watched=100,
                points=600,
                latest_activity_timestamp=datetime.datetime.now()
                )
            log.save()
