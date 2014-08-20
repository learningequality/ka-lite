"""Classes used by the student progress tastypie API"""

from django.core.exceptions import ObjectDoesNotExist

from kalite.facility.models import FacilityUser
from kalite.main.models import ExerciseLog, VideoLog
from kalite.playlist.models import VanillaPlaylist as Playlist, QuizLog
from kalite.topic_tools import get_slug2id_map, get_id2slug_map, get_flat_topic_tree, convert_leaf_url_to_id


FLAT_TOPIC_TREE = get_flat_topic_tree()
ID2SLUG_MAP = get_id2slug_map()
SLUG2ID_MAP = get_slug2id_map()

class PlaylistProgressParent:
    """Parent class for helpful class methods"""

    @classmethod
    def get_playlist_entry_ids(cls, playlist):
        """Return a tuple of the playlist's video ids and exercise ids as sets"""
        playlist_entries = playlist.get("entries")
        pl_video_ids = set([SLUG2ID_MAP.get(convert_leaf_url_to_id(entry["entity_id"])) for entry in playlist_entries if entry.get("entity_kind") == "Video"])
        pl_exercise_ids = set([convert_leaf_url_to_id(entry["entity_id"]) for entry in playlist_entries if entry.get("entity_kind") == "Exercise"])
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
        exists = True if [entry for entry in playlist_entries if entry["entity_kind"] == "Quiz"] else False
        try:
            quiz = QuizLog.objects.get(user=user, quiz=playlist_id)
        except ObjectDoesNotExist:
            quiz = None

        score = 0 if not quiz else int(float(quiz.total_correct) / float(quiz.total_number) * 100)

        return (exists, quiz, score)

class PlaylistProgress(PlaylistProgressParent):
    """Users progress on playlists"""

    def __init__(self, **kwargs):
        self.id = kwargs.get("id")
        self.title = kwargs.get("title")
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
        user = FacilityUser.objects.get(id=user_id)
        all_playlists = [pl.__dict__ for pl in Playlist.all()]

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user)

        exercise_ids = set([ex_log["exercise_id"] for ex_log in user_ex_logs])
        video_ids = set([ID2SLUG_MAP.get(vid_log["video_id"]) for vid_log in user_vid_logs])
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
            pl_video_ids, pl_exercise_ids = cls.get_playlist_entry_ids(p) 
            n_pl_videos = float(len(pl_video_ids))
            n_pl_exercises = float(len(pl_exercise_ids))

            # Vid & exercise logs in this playlist
            pl_ex_logs = [ex_log for ex_log in user_ex_logs if ex_log["exercise_id"] in pl_exercise_ids]
            pl_vid_logs = [vid_log for vid_log in user_vid_logs if vid_log["video_id"] in pl_video_ids]

            # Compute video stats 
            n_vid_complete = len([vid for vid in pl_vid_logs if vid["complete"]])
            n_vid_started = len([vid for vid in pl_vid_logs if (vid["total_seconds_watched"] > 0) and (not vid["complete"])])
            vid_pct_complete = int(float(n_vid_complete) / n_pl_videos * 100)
            vid_pct_started = int(float(n_vid_started) / n_pl_videos * 100) 
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
            elif ex_pct_struggling > 30:
                # TODO(dylan) are these ok limits? red progress bar if struggling with 30% or more  
                ex_status = "struggling" 
            elif ex_pct_mastered < 99:
                ex_status = "inprogress"
            else:
                ex_status = "complete"

            # Compute quiz stats
            quiz_exists, quiz_log, quiz_pct_score = cls.get_quiz_log(user, p.get("entries"), p.get("id"))
            if quiz_log:
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
    def user_progress_detail(cls, user_id, playlist_id):
        """
        Return a list of video, exercise, and quiz log PlaylistProgressDetail 
        objects associated with a specific user and playlist ID.
        """
        user = FacilityUser.objects.get(id=user_id)
        playlist = next((pl for pl in Playlist.all() if pl.id == playlist_id), None)
        playlist = playlist.__dict__

        pl_video_ids, pl_exercise_ids = cls.get_playlist_entry_ids(playlist) 

        # Retrieve video, exercise, and quiz logs that appear in this playlist
        user_vid_logs, user_ex_logs = cls.get_user_logs(user, pl_video_ids, pl_exercise_ids)

        # Used to store any progress the student has made on this playlist
        detailed_progress = dict()

        # Format & append exercises
        for log in user_ex_logs:
            if log.get("struggling"):
                status = "struggling"
            elif log.get("complete"):
                status = "complete"
            elif log.get("attempts"):
                status = "inprogress"
            else:
                status = "notstarted"

            log_id = log.get("exercise_id")
            log_entry = FLAT_TOPIC_TREE["Exercise"].get(log["exercise_id"])

            entry = {
                "id": log_id,
                "kind": "Exercise",
                "status": status,
                "score": log.get("streak_progress"),
                "title": log_entry["title"],
                "path": log_entry["path"],
            }

            detailed_progress[log_id] = cls(**entry)

        # Format & append videos
        for log in user_vid_logs:
            if log.get("complete"):
                status = "complete"
            elif log.get("total_seconds_watched"):
                status = "inprogress"
            else:
                status = "notstarted"

            log_id = log.get("video_id")
            log_entry = FLAT_TOPIC_TREE["Video"].get(log["video_id"])

            entry = {
                "id": log_id,
                "kind": "Video",
                "status": status,
                "score": int(float(log.get("points")) / float(750) * 100),
                "title": log_entry["title"],
                "path": log_entry["path"],
            }

            detailed_progress[log_id] = cls(**entry)

        # Format & append quiz
        quiz_exists, quiz_log, quiz_pct_score = cls.get_quiz_log(user, playlist.get("entries"), playlist.get("id"))

        # Format & append quizzes
        if quiz_exists and quiz_log:
            if quiz_log.complete:
                if quiz_pct_score <= 59:
                    status = "fail"
                elif quiz_pct_score <= 79:
                    status = "borderline"
                else:
                    status = "pass"
            elif quiz_log.attempts:
                status = "inprogress"
            else:
                status = "notstarted"

            log_id = quiz_log.quiz

            entry = {
                "id": log_id,
                "kind": "Quiz",
                "status": status,
                "score": quiz_pct_score,
                "title": playlist.get("title"),
                "path": "",
            }

            detailed_progress[log_id] = cls(**entry)

        # Finally, sort an ordered list of the playlist entries, with user progress
        # injected where it exists. 
        ordered_progress = list()
        for ent in playlist.get("entries"):
            kind = ent.get("entity_kind") 
            if kind == "Divider":
                continue
            elif kind == "Video":
                entity_id = SLUG2ID_MAP[(ent["entity_id"])]
            elif kind == "Exercise":
                entity_id = ent["entity_id"]
            elif kind == "Quiz":
                entity_id = playlist["id"]
            entry = detailed_progress.get(entity_id)   

            # Use the log if we have it, otherwise create an empty one.         
            if entry:
                ordered_progress.append(entry)
            else:
                if kind != "Quiz":
                    if kind == "Video":
                        topic_node = FLAT_TOPIC_TREE[kind].get(SLUG2ID_MAP[entity_id])
                    elif kind == "Exercise":
                        topic_node = FLAT_TOPIC_TREE[kind].get(entity_id)
                    title = topic_node["title"] 
                    path = topic_node["path"]
                else:
                    title = playlist["title"]
                    path = ""
                entry = {
                    "id": entity_id,
                    "kind": ent.get("entity_kind"),
                    "status": "notstarted",
                    "score": 0,
                    "title": title,
                    "path": path,
                }

                ordered_progress.append(cls(**entry))

        return ordered_progress