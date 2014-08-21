from kalite.main.models import VideoLog, ExerciseLog
from kalite.playlist.models import VanillaPlaylist as Playlist, QuizLog

class CreatePlaylistProgressMixin(object):
    """Helper to create progress for a student on a playlist"""

    @classmethod
    def create_playlist_progress(cls, user):
        default_playlist = "g3_p2"
        playlist = Playlist.all()[1]
        assert(playlist.id == default_playlist), "Unexpected playlist ID. Update tests to match new playlists.json"

        # Creating one specific entry for a specific item in the playlist 
        VideoLog(**{
            "user": user,
            "video_id": "nFsQA2Zvy1o",
            "youtube_id": "nFsQA2Zvy1o",
            "total_seconds_watched": 290,
            "points": 750,
            "complete": True,
        }).save()

        ExerciseLog(**{
            "user": user,
            "exercise_id": "comparing_whole_numbers",
            "streak_progress": 50,
            "attempts": 25,
            "points": 100,
            "complete": False,
            "struggling": True,
        }).save()

        QuizLog(**{
            "user": user,
            "quiz": default_playlist,
            "complete": True,
            "total_correct": 4,
            "total_number": 6,
        }).save()

        return playlist

class CreateTestLogMixin(object):
    DEFAULTS = {
        'test': 'g3_t1',  # this must be an actual exercise
        'index': '0',
        'complete': True,
        'started': True,
        'total_number': 4,
        'total_correct': 2,
    }
    @classmethod
    def create_test_log(cls, **kwargs):
        fields = CreateTestLogMixin.DEFAULTS.copy()
        fields['user'] = kwargs.get("user")
        # allow specification of totals and total correct, otherwise use default
        fields['total_number'] = kwargs.get("total_number", fields['total_number'])
        fields['total_correct'] = kwargs.get("total_correct", fields["total_correct"])

        return TestLog.objects.create(**fields)


class StudentTestingMixins(CreateTestLogMixin):
    '''
    Toplevel class that has all the mixin methods defined above
    '''
    pass