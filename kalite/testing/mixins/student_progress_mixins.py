import datetime

from kalite.main.models import AttemptLog, ExerciseLog, VideoLog
from kalite.student_testing.models import TestLog


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


class CreateAttemptLogMixin(object):
    DEFAULTS = {
        'exercise_id': 'comparing_whole_numbers',
        'timestamp': datetime.datetime.now(),
    }

    @classmethod
    def create_attempt_log(cls, **kwargs):
        fields = CreateAttemptLogMixin.DEFAULTS.copy()
        fields['user'] = kwargs.get("user")

        return AttemptLog.objects.create(**fields)

class CreateExerciseLogMixin(object):
    DEFAULTS = {
        'exercise_id': 'comparing_whole_numbers',
    }

    @classmethod
    def create_exercise_log(cls, **kwargs):
        fields = CreateExerciseLogMixin.DEFAULTS.copy()
        fields['user'] = kwargs.get("user")

        return ExerciseLog.objects.create(**fields)

class CreateVideoLogMixin(object):
    DEFAULTS = {
        'video_id': 'basic_addition',
        'youtube_id': 'xxxxxxxxxx',
    }

    @classmethod
    def create_video_log(cls, **kwargs):
        fields = CreateVideoLogMixin.DEFAULTS.copy()
        fields['user'] = kwargs.get("user")

        return VideoLog.objects.create(**fields)

class StudentProgressMixin(CreateTestLogMixin,
                           CreateAttemptLogMixin,
                           CreateExerciseLogMixin,
                           CreateVideoLogMixin):
    '''
    Toplevel class that has all the mixin methods defined above
    '''
    pass

