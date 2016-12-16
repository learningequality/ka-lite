"""
environment.py specific to the this app
"""

# These are auto-discovered by Behave? So nevermind that they're unused?
from kalite.testing.base_environment import before_all, after_all, before_feature, after_feature, before_scenario as base_before_scenario, after_scenario

import datetime

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog


def before_scenario(context, scenario):
    base_before_scenario(context, scenario)

    if "with_progress" in context.tags:
        user = FacilityUser.objects.get(username=context.user, facility=getattr(context, "facility", None))
        
        # Log 2 exercises, the first two, not some random exercises because
        # the tests should be consistent and the logged exercises need to
        # correlate with videos below if content recommendation should work
        exercises = context.content_exercises[:2]
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

        # Mark 2 videos watched, the first two, not some random videos because
        # the tests should be consistent...
        videos = context.content_videos[:2]

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
