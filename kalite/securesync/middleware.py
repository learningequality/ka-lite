class AuthFlag:
    def process_request(self, request):
        authflag = False
        if "facility_user" in request.session:
            authflag = request.session.get('facility_user').is_teacher
        if request.user.is_superuser:
            authflag = True
        request.is_admin = authflag