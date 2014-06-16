from kalite.facility.models import Facility, FacilityGroup, FacilityUser


class CreateFacilityMixin(object):
    DEFAULTS = {
        'name': 'facility0',
        'description': 'a default facility',
        'user_count': 1,
    }

    @classmethod
    def create_facility(cls, **kwargs):
        # we want this class's DEFAULTS, not whoever has inherited and thus overrided it!
        fields = CreateFacilityMixin.DEFAULTS.copy()
        fields.update(**kwargs)

        return Facility.objects.create(**fields)


class CreateGroupMixin(CreateFacilityMixin):
    DEFAULTS = {
        'name': 'group0',
    }

    @classmethod
    def create_group(cls, **kwargs):
        fields = CreateGroupMixin.DEFAULTS.copy()
        fields.update(**kwargs)
        fields['facility'] = (fields.get('facility') or
                              cls.create_facility(name='%s-facility' % fields['name']))
        return FacilityGroup.objects.create(**fields)


class CreateStudentMixin(CreateFacilityMixin):
    DEFAULTS = {
        'first_name': 'Cannon',
        'last_name': 'Fodder',
        'username': 'teststudent1',
        'is_teacher': False,
    }

    @classmethod
    def create_student(cls, password='password', **kwargs):
        fields = CreateStudentMixin.DEFAULTS.copy()
        fields.update(**kwargs)
        fields['facility'] = (fields.get('facility') or
                              cls.create_facility(name='%s-facility' % fields['username']))
        user = FacilityUser(**fields)
        user.set_password(password)
        user.save()
        return user


class CreateTeacherMixin(CreateStudentMixin):
    DEFAULTS = {
        'first_name': 'terror',
        'last_name': 'teacher',
        'username': 'testteacher1',
        'password': 'password',
        'is_teacher': True,
    }

    @classmethod
    def create_teacher(cls, **kwargs):
        fields = CreateTeacherMixin.DEFAULTS.copy()
        fields.update(**kwargs)
        return cls.create_student(**fields)  # delegate to the create_student method, which has the right logic


class FacilityMixins(CreateTeacherMixin, CreateStudentMixin, CreateGroupMixin, CreateFacilityMixin):
    '''
    Toplevel class that has all the mixin methods defined above
    '''
    pass
