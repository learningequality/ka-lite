import datetime 

from kalite.main.models import AttemptLog, ExerciseLog

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