class AuthFlag:
    def process_request(self,request):
        authflag = False
        if request.session.get('facility_user'):
            if request.session.get('facility_user').is_teacher:
                authflag = True
        elif request.user.is_superuser:
            authflag = True
        request.authflag = authflag