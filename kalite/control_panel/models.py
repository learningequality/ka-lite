"""Classes used by the student progress tastypie API"""

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.playlist.models import VanillaPlaylist as Playlist, QuizLog
from kalite.topic_tools import get_slug2id_map, get_id2slug_map, get_flat_topic_tree, convert_leaf_url_to_id

class UserPlaylistProgress:
    """Users progress on playlists"""

    def __init__(self, **kwargs):
        self.user_id = kwargs.get("user_id")
        self.playlists = kwargs.get("playlists")

    @classmethod
    def user_playlist_progress(cls, user_id):
        """
        Return a dictionary of playlists that the user has started, with stats on completion_timestamp
        Response schema:
            [
                {
                    "grade": "tag_name",
                    "playlists": [
                        {
                            "insert_existing_playlist_data": "...",
                            "...": "...",
                            "vid_stats": {
                                "pct_complete": "...",
                                "pct_started": "...",
                            },
                            "ex_stats": {
                                "pct_mastered": "...",
                                "pct_inprogress": "...",
                                "pct_struggling": "...",
                                "pct_incomplete": "...",
                            },
                            "test_stats": {
                                "pct_score": "...",
                            }
                        },
                        {
                            "insert_existing_playlist_data": "...",
                            "...": "..."
                        },
                    ]
                }
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
        for i, p in enumerate(user_playlists):
            # Playlist entry totals
            pl_video_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in p.get("entries") if entry.get("entity_kind") == "Video"])
            pl_exercise_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in p.get("entries") if entry.get("entity_kind") == "Exercise"])
            n_pl_videos = len(pl_video_ids)
            n_pl_exercises = len(pl_exercise_ids) 

            # Vid & exercise logs in this playlist
            ex_logs = [ex_log for ex_log in exercise_logs if ex_log["exercise_id"] in pl_exercise_ids]
            vid_logs = [vid_log for vid_log in video_logs if id2slug_map.get(vid_log["video_id"]) in pl_video_ids]
            n_ex_logs = len(ex_logs)
            n_vid_logs = len(vid_logs)

            # Compute video stats 
            vid_stats = {
                "pct_complete": len([vid for vid in vid_logs if vid["complete"]])/float(n_pl_videos),
                "pct_started": len([vid for vid in vid_logs if (vid["total_seconds_watched"] > 0) and (not vid["complete"])])/float(n_pl_videos),
            }
            # Compute exercise stats 
            ex_stats = {
                "pct_mastered": len([ex for ex in ex_logs if ex["complete"]])/float(n_pl_exercises),
                "pct_started": len([ex for ex in ex_logs if (ex["attempts"] > 0) and (not ex["complete"])])/float(n_pl_exercises),
                "pct_struggling": len([ex for ex in ex_logs if ex["struggling"]])/float(n_pl_exercises),
            }
            # Compute test stats
            quiz_exists = True if [entry for entry in p.get("entries") if entry["entity_kind"] == "Quiz"] else False
            quiz_result = None if not quiz_exists else QuizLog.objects.filter(user=user, quiz=p.get("id"))
            quiz_stats = {
                "quiz_exists": quiz_exists,
                "pct_score": 0 if not quiz_result else float(quiz_result.total_correct) / float(quiz_result.total_number),
            }

            user_playlists[i]["vid_stats"] = vid_stats
            user_playlists[i]["ex_stats"] = ex_stats
            user_playlists[i]["quiz_stats"] = quiz_stats            

        return user_playlists
        # Create a new UserPlaylistProgress model and return it 