"""Classes used by the student progress tastypie API"""
import json
from fle_utils.config.models import Settings

from django.conf import settings
from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.topic_tools.content_models import get_topic_node, get_content_parents, get_topic_contents, get_content_item,  get_topic_nodes


class PlaylistProgressParent:
    """Parent class for helpful class methods"""

    @classmethod
    def get_playlist_entry_ids(cls, playlist):
        """Return a tuple of the playlist's video ids and exercise ids as sets"""
        items = get_topic_contents(topic_id=playlist.get("id"))
        pl_video_ids = set([item.get("id") for item in items if item.get("kind") == "Video"])
        pl_exercise_ids = set([item.get("id") for item in items if item.get("kind") == "Exercise"])
        return (pl_video_ids, pl_exercise_ids)

    @classmethod
    def get_user_logs(cls, user, pl_video_ids=None, pl_exercise_ids=None):
        user_ex_logs = list(ExerciseLog.objects \
            .filter(user=user) \
            .values("exercise_id", "complete", "points", "attempts", "streak_progress", "struggling", "completion_timestamp"))
        user_vid_logs = list(VideoLog.objects \
            .filter(user=user) \
            .values("video_id", "complete", "total_seconds_watched", "points", "completion_timestamp"))

        if pl_video_ids and pl_exercise_ids:
            user_ex_logs = [ex_log for ex_log in user_ex_logs if ex_log.get("exercise_id") in pl_exercise_ids]
            user_vid_logs = [vid_log for vid_log in user_vid_logs if vid_log.get("video_id") in pl_video_ids]

        return (user_vid_logs, user_ex_logs)


class PlaylistProgress(PlaylistProgressParent):
    """Users progress on playlists"""

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @classmethod
    def user_progress(cls, user_id, language=None):
        """
        Return a list of PlaylistProgress objects associated with the user.
        """

        if not language:
            language = Settings.get("default_language") or settings.LANGUAGE_CODE

        user = FacilityUser.objects.get(id=user_id)

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user)

        exercise_ids = list(set([ex_log["exercise_id"] for ex_log in user_ex_logs]))
        video_ids = list(set([vid_log["video_id"] for vid_log in user_vid_logs]))

        # Build a list of playlists for which the user has at least one data point
        user_playlists = get_content_parents(ids=exercise_ids+video_ids, language=language)

        # Store stats for each playlist
        user_progress = list()
        for i, p in enumerate(user_playlists):
            # Playlist entry totals
            pl_video_ids, pl_exercise_ids = cls.get_playlist_entry_ids(p)
            n_pl_videos = float(len(pl_video_ids))
            n_pl_exercises = float(len(pl_exercise_ids))

            # Vid & exercise logs in this playlist
            pl_ex_logs = [ex_log for ex_log in user_ex_logs if ex_log["exercise_id"] in pl_exercise_ids]
            pl_vid_logs = [vid_log for vid_log in user_vid_logs if vid_log["video_id"] in pl_video_ids]

            # Compute video stats
            n_vid_complete = len([vid for vid in pl_vid_logs if vid["complete"]])
            n_vid_started = len([vid for vid in pl_vid_logs if (vid["total_seconds_watched"] > 0) and (not vid["complete"])])
            vid_pct_complete = int(float(n_vid_complete) / n_pl_videos * 100) if n_pl_videos else 0
            vid_pct_started = int(float(n_vid_started) / n_pl_videos * 100) if n_pl_videos else 0
            if vid_pct_complete == 100:
                vid_status = "complete"
            elif n_vid_started > 0:
                vid_status = "inprogress"
            else:
                vid_status = "notstarted"

            # Compute exercise stats
            n_ex_mastered = len([ex for ex in pl_ex_logs if ex["complete"]])
            n_ex_started = len([ex for ex in pl_ex_logs if ex["attempts"] > 0])
            n_ex_incomplete = len([ex for ex in pl_ex_logs if (ex["attempts"] > 0 and not ex["complete"])])
            n_ex_struggling = len([ex for ex in pl_ex_logs if ex["struggling"]])
            ex_pct_mastered = int(float(n_ex_mastered) / (n_pl_exercises or 1) * 100)
            ex_pct_incomplete = int(float(n_ex_incomplete) / (n_pl_exercises or 1) * 100)
            ex_pct_struggling = int(float(n_ex_struggling) / (n_pl_exercises or 1) * 100)
            if not n_ex_started:
                ex_status = "notstarted"
            elif ex_pct_struggling > 0:
                # note: we want to help students prioritize areas they need to focus on
                # therefore if they are struggling in this exercise group, we highlight it for them
                ex_status = "struggling"
            elif ex_pct_mastered < 99:
                ex_status = "inprogress"
            else:
                ex_status = "complete"

            progress = {
                "title": p.get("title"),
                "id": p.get("id"),
                "tag": p.get("tag"),
                "vid_pct_complete": vid_pct_complete,
                "vid_pct_started": vid_pct_started,
                "vid_status": vid_status,
                "ex_pct_mastered": ex_pct_mastered,
                "ex_pct_incomplete": ex_pct_incomplete,
                "ex_pct_struggling": ex_pct_struggling,
                "ex_status": ex_status,
                "n_pl_videos": n_pl_videos,
                "n_pl_exercises": n_pl_exercises,
            }

            try:
                progress["url"] = reverse("view_playlist", kwargs={"playlist_id": p.get("id")})
            except NoReverseMatch:
                progress["url"] = reverse("learn") + p.get("path")

            user_progress.append(cls(**progress))

        return user_progress

class PlaylistProgressDetail(PlaylistProgressParent):
    """Detailed progress on a specific playlist for a specific user"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.title = kwargs.get("title")
        self.kind = kwargs.get("kind")
        self.status = kwargs.get("status")
        self.score = kwargs.get("score")
        self.path = kwargs.get("path")

    @classmethod
    def user_progress_detail(cls, user_id, playlist_id, language=None):
        """
        Return a list of video, exercise, and quiz log PlaylistProgressDetail
        objects associated with a specific user and playlist ID.
        """
        user = FacilityUser.objects.get(id=user_id)
        playlist = get_topic_node(content_id=playlist_id)

        pl_video_ids, pl_exercise_ids = cls.get_playlist_entry_ids(playlist)

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user, pl_video_ids, pl_exercise_ids)

        # Finally, sort an ordered list of the playlist entries, with user progress
        # injected where it exists.
        progress_details = list()
        for leaf_node in get_topic_nodes(parent=playlist_id, language=language):
            entity_id = leaf_node.get("id")
            kind = leaf_node.get("kind")

            status = "notstarted"
            score = 0

            if kind == "Video":
                vid_log = next((vid_log for vid_log in user_vid_logs if vid_log["video_id"] == entity_id), None)
                if vid_log:
                    if vid_log.get("complete"):
                        status = "complete"
                    elif vid_log.get("total_seconds_watched"):
                        status = "inprogress"

                    score = int(float(vid_log.get("points")) / float(750) * 100)

            elif kind == "Exercise":
                ex_log = next((ex_log for ex_log in user_ex_logs if ex_log["exercise_id"] == entity_id), None)
                if ex_log:
                    if ex_log.get("struggling"):
                        status = "struggling"
                    elif ex_log.get("complete"):
                        status = "complete"
                    elif ex_log.get("attempts"):
                        status = "inprogress"

                    score = ex_log.get('streak_progress')

            progress_details.append(PlaylistProgressDetail(
                id=entity_id,
                title=leaf_node["title"],
                kind=kind,
                status=status,
                score=score,
                path=leaf_node["path"]
            ))

        return progress_details
