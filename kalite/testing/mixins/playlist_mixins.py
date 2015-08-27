from kalite.main.models import ExerciseLog
from kalite.playlist.models import VanillaPlaylist as Playlist, QuizLog


class CreatePlaylistProgressMixin(object):
    """Helper to create progress for a student on a playlist"""

    @classmethod
    def create_playlist_progress(cls, user, quiz=True):
        default_playlist = "g4_u401_p1"
        playlist = [pl for pl in Playlist.all() if pl.id == default_playlist]
        assert(playlist[0].id == default_playlist), "Unexpected playlist ID. Update tests to match new playlists.json"
        playlist = playlist[0]

        # Creating one specific entry for a specific item in the playlist
        # Note (aron): The new nalanda playlists don't have any videos now
        # So I commented those out
        # VideoLog(**{
        #     "user": user,
        #     "video_id": "nFsQA2Zvy1o",
        #     "youtube_id": "nFsQA2Zvy1o",
        #     "total_seconds_watched": 290,
        #     "points": 750,
        #     "complete": True,
        # }).save()

        ExerciseLog(**{
            "user": user,
            "exercise_id": "telling_time",
            "streak_progress": 50,
            "attempts": 25,
            "points": 100,
            "complete": False,
            "struggling": True,
        }).save()

        if quiz:
            QuizLog(**{
                "user": user,
                "quiz": default_playlist,
                "complete": True,
                "attempts": 1,
                "response_log": "[4]",
                "total_correct": 4,
                "total_number": 6,
            }).save()

        return playlist
