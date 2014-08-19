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
        self.vid_status = kwargs.get("vid_status")
        self.ex_pct_mastered = kwargs.get("ex_pct_mastered")
        self.ex_pct_incomplete = kwargs.get("ex_pct_incomplete")
        self.ex_pct_struggling = kwargs.get("ex_pct_struggling")
        self.ex_status = kwargs.get("ex_status")
        self.quiz_exists = kwargs.get("quiz_exists")
        self.quiz_status = kwargs.get("quiz_status")
        self.quiz_pct_score = kwargs.get("quiz_pct_score")

    @classmethod
    def user_progress(cls, user_id):
        """
        Return a list of PlaylistProgress objects associated with the user.
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
        quiz_log_ids = QuizLog.objects.filter(user=user).values("quiz")
        
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
            # After checking for video & exercise log matches in a playlist, 
            # do a final pass for quizzes in case the kid jumped right to the quiz 
            for ql in quiz_log_ids:
                if p.get("id") == ql["quiz"] and not next((pl for pl in user_playlists if pl.get("id") == p.get("id")), None):
                    user_playlists.append(p)


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
            n_vid_complete = len([vid for vid in vid_logs if vid["complete"]])
            n_vid_started = len([vid for vid in vid_logs if (vid["total_seconds_watched"] > 0) and (not vid["complete"])])
            vid_pct_complete = int(float(n_vid_complete) / n_pl_videos * 100)
            vid_pct_started = int(float(n_vid_started) / n_pl_videos * 100) 
            if vid_pct_complete == 100:
                vid_status = "complete"
            elif n_vid_started > 0:
                vid_status = "inprogress"
            else:
                vid_status = "notstarted" 

            # Compute exercise stats 
            n_ex_mastered = len([ex for ex in ex_logs if ex["complete"]])
            n_ex_started = len([ex for ex in ex_logs if ex["attempts"] > 0])
            n_ex_incomplete = len([ex for ex in ex_logs if (ex["attempts"] > 0 and not ex["complete"])])
            n_ex_struggling = len([ex for ex in ex_logs if ex["struggling"]])
            ex_pct_mastered = int(float(n_ex_mastered) / n_pl_exercises * 100) 
            ex_pct_incomplete = int(float(n_ex_incomplete) / n_pl_exercises * 100) 
            ex_pct_struggling = int(float(n_ex_struggling) / n_pl_exercises * 100) 
            if not n_ex_started:
                ex_status = "notstarted"
            elif ex_pct_struggling > 30:
                ex_status = "struggling" # TODO(dylan) are these ok limits?
            elif ex_pct_mastered < 99:
                ex_status = "inprogress"
            else:
                ex_status = "complete"

            # Compute test stats
            quiz_exists = True if [entry for entry in p.get("entries") if entry["entity_kind"] == "Quiz"] else False
            quiz_result = None if not quiz_exists else QuizLog.objects.filter(user=user, quiz=p.get("id"))
            quiz_pct_score = 0 if not quiz_result else int(float(quiz_result[0].total_correct) / float(quiz_result[0].total_number) * 100)
            if quiz_result:
                if quiz_pct_score <= 50:
                    quiz_status = "struggling"
                elif quiz_pct_score <= 79:
                    quiz_status = "borderline"
                else:
                    quiz_status = "complete"
            else:
                quiz_status = "notstarted"

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
                "quiz_status": quiz_status,
                "quiz_exists": quiz_exists,
                "quiz_pct_score": quiz_pct_score,
            }

            user_progress.append(cls(**progress))
                    
        return user_progress

class PlaylistProgressDetail:
    """Detailed progress on a specific playlist for a specific user"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.kind = kwargs.get("kind")
        self.status = kwargs.get("status")
        self.description = kwargs.get("description")

    @classmethod
    def user_progress_detail(cls, user_id, playlist_id):
        """
        Return a list of video, exercise, and quiz log PlaylistProgressDetail objects associated with a specific user and playlist ID.
        """

        user = FacilityUser.objects.filter(id=user_id)
        playlist = next((pl for pl in Playlist.all() if pl.id == playlist_id), None)
        playlist = playlist.__dict__
        flat_topic_tree = get_flat_topic_tree()
        id2slug_map = get_id2slug_map()
        slug2id_map = get_slug2id_map()

        pl_video_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in playlist.get("entries") if entry.get("entity_kind") == "Video"])
        pl_exercise_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in playlist.get("entries") if entry.get("entity_kind") == "Exercise"])

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        ex_logs = list(ExerciseLog.objects \
            .filter(user=user, exercise_id__in=pl_exercise_ids) \
            .values("exercise_id", "complete", "points", "attempts", "streak_progress", "struggling", "completion_timestamp"))
        vid_logs = list(VideoLog.objects \
            .filter(user=user, video_id__in=pl_video_ids) \
            .values("video_id", "complete", "total_seconds_watched", "points", "completion_timestamp"))
        quiz_exists = True if [entry for entry in playlist.get("entries") if entry["entity_kind"] == "Quiz"] else False
        quiz_result = None if not quiz_exists else list(QuizLog.objects \
            .filter(user=user, quiz=playlist.get("id"))
            .values("complete", "quiz", "total_number", "attempts", "total_correct"))

        detailed_progress = list()

        # Format & append exercises
        for log in ex_logs:
            if log.get("struggling"):
                status = "struggling"
            elif log.get("complete"):
                status = "complete"
            elif log.get("attempts"):
                status = "inprogress"
            else:
                status = "notstarted"

            entry = {
                "id": log.get("exercise_id"),
                "kind": "Exercise",
                "status": status,
                "description": "Blah blah I'm an exercise",
            }

            detailed_progress.append(cls(**entry))

        # Format & append videos
        for log in vid_logs:
            if log.get("complete"):
                status = "complete"
            elif log.get("total_seconds_watched"):
                status = "inprogress"
            else:
                status = "notstarted"
            entry = {
                "id": log.get("video_id"),
                "kind": "Video",
                "status": status,
                "description": "Blah blah I'm a video"
            }

            detailed_progress.append(cls(**entry))

        # Format & append quizzes
        if quiz_exists and quiz_result:
            quiz_result = quiz_result[0] 
            if quiz_result.get("complete"):
                pct_score = 100 * (float(quiz_result.get("total_correct")) / float(quiz_result.get("total_number")))  
                if pct_score <= 59:
                    status = "fail"
                elif pct_score <= 79:
                    status = "borderline"
                else:
                    status = "pass"    
                status = "complete"
            elif quiz_result.get("attempts"):
                status = "inprogress"
            else:
                status = "notstarted"
            entry = {
                "id": quiz_result.get("quiz"),
                "kind": "Quiz",
                "status": status,
                "description": "Blah blah I'm a quiz",
            }

            detailed_progress.append(cls(**entry))

        return detailed_progress