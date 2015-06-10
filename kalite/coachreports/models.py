"""Classes used by the student progress tastypie API"""
import json

from django.core.urlresolvers import reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.playlist.models import QuizLog
from kalite.topic_tools import get_id2slug_map, get_leafed_topics, get_content_cache, get_exercise_cache, get_node_cache

class PlaylistProgressParent:
    """Parent class for helpful class methods"""

    @classmethod
    def get_playlist_entry_ids(cls, playlist):
        """Return a tuple of the playlist's video ids and exercise ids as sets"""
        playlist_entries = playlist.get("children")
        topic_cache = get_node_cache()["Topic"]
        pl_video_ids = set([id for id in playlist_entries if topic_cache.get(id).get("kind") == "Video"])
        pl_exercise_ids = set([id for id in playlist_entries if topic_cache.get(id).get("kind") == "Exercise"])
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

    @classmethod
    def get_quiz_log(cls, user, playlist_entries, playlist_id):
        exists = True if [entry for entry in playlist_entries if entry.get("entity_kind") == "Quiz"] else False
        try:
            quiz = QuizLog.objects.get(user=user, quiz=playlist_id)
        except ObjectDoesNotExist:
            quiz = None

        if quiz:
            score = int(float(json.loads(quiz.response_log)[quiz.attempts-1]) / float(quiz.total_number) * 100)
        else:
            score = 0

        return (exists, quiz, score)

class PlaylistProgress(PlaylistProgressParent):
    """Users progress on playlists"""

    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

    @classmethod
    def user_progress(cls, user_id):
        """
        Return a list of PlaylistProgress objects associated with the user.
        """
        user = FacilityUser.objects.get(id=user_id)
        all_playlists = get_leafed_topics()

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user)

        exercise_ids = set([ex_log["exercise_id"] for ex_log in user_ex_logs])
        video_ids = set([get_id2slug_map().get(vid_log["video_id"]) for vid_log in user_vid_logs])
        # quiz_log_ids = [ql_id["quiz"] for ql_id in QuizLog.objects.filter(user=user).values("quiz")]
        # Build a list of playlists for which the user has at least one data point
        user_playlists = list()
        for p in all_playlists:
            for e_id in p.get("children"):

                if e_id in exercise_ids or e_id in video_ids:
                    user_playlists.append(p)
                    break

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
            ex_pct_mastered = int(float(n_ex_mastered) / n_pl_exercises * 100)
            ex_pct_incomplete = int(float(n_ex_incomplete) / n_pl_exercises * 100)
            ex_pct_struggling = int(float(n_ex_struggling) / n_pl_exercises * 100)
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

            # Oh Quizzes, we hardly knew ye!
            # TODO (rtibbles): Sort out the status of Quizzes, and either reinstate them or remove them.
            # Compute quiz stats
            # quiz_exists, quiz_log, quiz_pct_score = cls.get_quiz_log(user, (p.get("entries") or p.get("children")), p.get("id"))
            # if quiz_log:
            #     if quiz_pct_score <= 50:
            #         quiz_status = "struggling"
            #     elif quiz_pct_score <= 79:
            #         quiz_status = "borderline"
            #     else:
            #         quiz_status = "complete"
            # else:
            #     quiz_status = "notstarted"

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
                # "quiz_status": quiz_status,
                # "quiz_exists": quiz_exists,
                # "quiz_pct_score": quiz_pct_score,
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
    def create_empty_entry(cls, entity_id, kind, playlist):
        if kind != "Quiz":
            if kind == "Video":
                topic_node = get_content_cache().get(entity_id)
            elif kind == "Exercise":
                topic_node = get_exercise_cache().get(entity_id)
            title = topic_node["title"]
            path = topic_node["path"]
        else:
            title = playlist["title"]
            path = ""
        entry = {
            "id": entity_id,
            "kind": kind,
            "status": "notstarted",
            "score": 0,
            "title": title,
            "path": path,
        }

        return entry

    @classmethod
    def user_progress_detail(cls, user_id, playlist_id):
        """
        Return a list of video, exercise, and quiz log PlaylistProgressDetail
        objects associated with a specific user and playlist ID.
        """
        user = FacilityUser.objects.get(id=user_id)
        playlist = next((pl for pl in get_leafed_topics() if pl.get("id") == playlist_id), None)

        pl_video_ids, pl_exercise_ids = cls.get_playlist_entry_ids(playlist)

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user, pl_video_ids, pl_exercise_ids)

        # Format & append quiz the quiz log, if it exists
        # quiz_exists, quiz_log, quiz_pct_score = cls.get_quiz_log(user, (playlist.get("entries") or playlist.get("children")), playlist.get("id"))

        # Finally, sort an ordered list of the playlist entries, with user progress
        # injected where it exists.
        progress_details = list()
        for entity_id in playlist.get("children"):
            entry = {}
            leaf_node = get_content_cache().get(entity_id, get_exercise_cache().get(entity_id, {}))
            kind = leaf_node.get("kind")

            if kind == "Video":
                vid_log = next((vid_log for vid_log in user_vid_logs if vid_log["video_id"] == entity_id), None)
                if vid_log:
                    if vid_log.get("complete"):
                        status = "complete"
                    elif vid_log.get("total_seconds_watched"):
                        status = "inprogress"
                    else:
                        status = "notstarted"

                    entry = {
                        "id": entity_id,
                        "kind": kind,
                        "status": status,
                        "score": int(float(vid_log.get("points")) / float(750) * 100),
                        "title": leaf_node["title"],
                        "path": leaf_node["path"],
                    }

            elif kind == "Exercise":
                ex_log = next((ex_log for ex_log in user_ex_logs if ex_log["exercise_id"] == entity_id), None)
                if ex_log:
                    if ex_log.get("struggling"):
                        status = "struggling"
                    elif ex_log.get("complete"):
                        status = "complete"
                    elif ex_log.get("attempts"):
                        status = "inprogress"

                    entry = {
                        "id": entity_id,
                        "kind": kind,
                        "status": status,
                        "score": ex_log.get("streak_progress"),
                        "title": leaf_node["title"],
                        "path": leaf_node["path"],
                    }

            # Oh Quizzes, we hardly knew ye!
            # TODO (rtibbles): Sort out the status of Quizzes, and either reinstate them or remove them.
            # Quizzes were introduced to provide a way of practicing multiple types of exercise at once
            # However, there is currently no way to access them, and the manner for generating them (from the now deprecated Playlist models) is inaccessible
            # elif kind == "Quiz":
            #     entity_id = playlist["id"]
            #     if quiz_log:
            #         if quiz_log.complete:
            #             if quiz_pct_score <= 59:
            #                 status = "fail"
            #             elif quiz_pct_score <= 79:
            #                 status = "borderline"
            #             else:
            #                 status = "pass"
            #         elif quiz_log.attempts:
            #             status = "inprogress"
            #         else:
            #             status = "notstarted"

            #         quiz_log_id = quiz_log.quiz

            #         entry = {
            #             "id": quiz_log_id,
            #             "kind": "Quiz",
            #             "status": status,
            #             "score": quiz_pct_score,
            #             "title": playlist.get("title"),
            #             "path": "",
            #         }

            if not entry:
                entry = cls.create_empty_entry(entity_id, kind, playlist)

            progress_details.append(cls(**entry))

        return progress_details
