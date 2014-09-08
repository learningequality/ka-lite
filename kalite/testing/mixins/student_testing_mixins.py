from kalite.student_testing.models import TestLog, Test


class CreateTestLogMixin(object):
    DEFAULTS = {
        'test': 'g3_t1',  # this must be an actual exercise
        'index': '0',
        'complete': True,
        'started': True,
 }
    @classmethod
    def create_test_log(cls, **kwargs):
        fields = CreateTestLogMixin.DEFAULTS.copy()
        test_object = Test.all()[kwargs.get("test", fields["test"])]
        total_questions = test_object.total_questions
        fields['user'] = kwargs.get("user")
        # allow specification of totals and total correct, otherwise use default
        fields['total_number'] = kwargs.get("total_number", total_questions)
        fields['total_correct'] = kwargs.get("total_correct", total_questions / 2)
        return TestLog.objects.create(**fields)


class StudentTestingMixins(CreateTestLogMixin):
    '''
    Toplevel class that has all the mixin methods defined above
    '''
    pass
