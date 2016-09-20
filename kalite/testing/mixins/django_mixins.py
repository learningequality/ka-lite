from django.contrib.auth.models import User


class CreateAdminMixin:
    DEFAULTS = {
        'username': 'admin',
        'password': 'admin',
        'email': 'admin@admin.com',
        'is_superuser': True,
        'is_staff': True,
    }

    @classmethod
    def create_admin(cls, **kwargs):
        fields = CreateAdminMixin.DEFAULTS.copy()
        fields.update(**kwargs)
        u = User(**fields)
        u.set_password(fields['password'])
        u.save()
        return u
