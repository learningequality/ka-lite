from django.contrib.auth.models import User


class CreateAdminMixin:
    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "admin"
    ADMIN_EMAIL = "admin@admin.com"

    @classmethod
    def create_admin(cls, username=ADMIN_USERNAME, password=ADMIN_PASSWORD, email=ADMIN_EMAIL):
        u = User(username=username, email=email)
        u.set_password(password)
        u.save()
        return u
