"""Classes used by the student progress tastypie API"""

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.playlist.models import VanillaPlaylist as Playlist, QuizLog
from kalite.topic_tools import get_slug2id_map, get_id2slug_map, get_flat_topic_tree, convert_leaf_url_to_id

class PlaylistProgress:
    """Users progress on playlists"""

    def __init__(self, **kwargs):
        self.title = kwargs.get("title")
        self.id = kwargs.get("id")
        self.tag = kwargs.get("tag")
        self.vid_pct_complete = kwargs.get("vid_pct_complete")
        self.vid_pct_started = kwargs.get("vid_pct_started")
        self.ex_pct_mastered = kwargs.get("ex_pct_mastered")
        self.ex_pct_struggling = kwargs.get("ex_pct_struggling")
        self.ex_pct_started = kwargs.get("ex_pct_started")
        self.quiz_exists = kwargs.get("quiz_exists")
        self.quiz_pct_score = kwargs.get("quiz_pct_score")

    @classmethod
    def user_progress(cls, user_id):
        """
        Return a list of PlaylistProgress objects associated with the user.
            [
                {
                    "title": "...",
                    "id": "...",
                    "tag": "...",
                    "vid_pct_complete": "...",
                    "vid_pct_started": "...",
                    "ex_pct_mastered": "...",
                    "ex_pct_struggling": "...",
                    "ex_pct_started": "...",
                    "quiz_exists": "...",
                    "quiz_pct_score": "...",
                },
                { ... etc ... }
            ]
        """
        user = FacilityUser.objects.filter(id=user_id)
        all_playlists = [pl.__dict__ for pl in Playlist.all()]
        flat_topic_tree = get_flat_topic_tree()
        id2slug_map = get_id2slug_map()
        slug2id_map = get_slug2id_map()

        exercise_logs = list(ExerciseLog.objects \
            .filter(user=user) \
            .values("exercise_id", "complete", "points", "attempts", "streak_progress", "struggling", "completion_timestamp"))
        video_logs = list(VideoLog.objects \
            .filter(user=user) \
            .values("video_id", "complete", "total_seconds_watched", "points", "completion_timestamp"))

        exercise_ids = set([ex_log["exercise_id"] for ex_log in exercise_logs])
        video_ids = set([id2slug_map.get(vid_log["video_id"]) for vid_log in video_logs])
        
        # Build a list of playlists for which the user has at least one data point 
        ## TODO(dylan) this won't pick up playlists the user is assigned but has not started yet. 
        user_playlists = list()
        for p in all_playlists:
            for e in p.get("entries"):
                if e.get("entity_kind") == "Video" or e.get("entity_kind") == "Exercise":
                    entity_id = convert_leaf_url_to_id(e.get("entity_id"))

                    if entity_id in exercise_ids or entity_id in video_ids:
                        user_playlists.append(p)
                        break

        # Store stats for each playlist
        user_progress = list()
        for i, p in enumerate(user_playlists):
            # Playlist entry totals
            pl_video_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in p.get("entries") if entry.get("entity_kind") == "Video"])
            pl_exercise_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in p.get("entries") if entry.get("entity_kind") == "Exercise"])
            n_pl_videos = float(len(pl_video_ids))
            n_pl_exercises = float(len(pl_exercise_ids))

            # Vid & exercise logs in this playlist
            ex_logs = [ex_log for ex_log in exercise_logs if ex_log["exercise_id"] in pl_exercise_ids]
            vid_logs = [vid_log for vid_log in video_logs if id2slug_map.get(vid_log["video_id"]) in pl_video_ids]

            # Compute video stats 
            vid_pct_complete = float(len([vid for vid in vid_logs if vid["complete"]])) / n_pl_videos
            vid_pct_started = float(len([vid for vid in vid_logs if (vid["total_seconds_watched"] > 0) and (not vid["complete"])])) / n_pl_videos

            # Compute exercise stats 
            ex_pct_mastered = float(len([ex for ex in ex_logs if ex["complete"]])) / n_pl_exercises
            ex_pct_started = float(len([ex for ex in ex_logs if (ex["attempts"] > 0) and (not ex["complete"])])) / n_pl_exercises
            ex_pct_struggling = float(len([ex for ex in ex_logs if ex["struggling"]])) / n_pl_exercises

            # Compute test stats
            quiz_exists = True if [entry for entry in p.get("entries") if entry["entity_kind"] == "Quiz"] else False
            quiz_result = None if not quiz_exists else QuizLog.objects.filter(user=user, quiz=p.get("id"))
            quiz_pct_score = 0 if not quiz_result else float(quiz_result.total_correct) / float(quiz_result.total_number)

            progress = {
                "title": p.get("title"),
                "id": p.get("id"),
                "tag": p.get("tag"),
                "vid_pct_complete": vid_pct_complete,
                "vid_pct_started": vid_pct_started,
                "ex_pct_mastered": ex_pct_mastered,
                "ex_pct_struggling": ex_pct_struggling,
                "ex_pct_started": ex_pct_started,
                "quiz_exists": quiz_exists,
                "quiz_pct_score": quiz_pct_score,
            }

            user_progress.append(cls(**progress))
                    
        return user_progress
