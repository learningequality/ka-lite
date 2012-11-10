class AuthFlags:
    def process_request(self,request):
        request.is_admin = False
        request.is_teacher = False
        request.is_logged_in = False
        request.only_admin = False
        if request.session.get('facility_user'):
            if request.session.get('facility_user').is_teacher:
                request.is_admin = True
                request.is_teacher = True
                request.is_logged_in = True
        elif request.user.is_superuser:
            request.is_admin = True
        if request.user.is_authenticated():
        	request.is_logged_in = True
        if request.is_admin and not request.is_teacher:
        	request.only_admin = True

