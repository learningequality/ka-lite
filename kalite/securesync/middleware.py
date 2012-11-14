class AuthFlags:
    def process_request(self,request):
        request.is_admin = False
        request.is_teacher = False
        request.is_logged_in = False
        request.is_django_user = False

        if request.session.get('facility_user'):
            if request.session.get('facility_user').is_teacher:
                request.is_admin = True
                request.is_teacher = True
                request.is_logged_in = True
        elif request.user.is_superuser:
            request.is_admin = True
            request.is_django_user = True
        if request.user.is_authenticated():
            request.is_logged_in = True

