from .models import Facility


class AuthFlags:
    def process_request(self, request):
        request.is_admin = False
        request.is_teacher = False
        request.is_logged_in = False
        request.is_django_user = False

        if request.user.is_authenticated():
            request.is_logged_in = True
            request.is_django_user = True
            if request.user.is_superuser:
                request.is_admin = True
            if "facility_user" in request.session:
                del request.session["facility_user"]
        elif "facility_user" in request.session:
            if request.session["facility_user"].is_teacher:
                request.is_admin = True
                request.is_teacher = True
            request.is_logged_in = True

class FacilityCheck:
    def process_request(self, request):
        """
        Cache facility data in the session,
          while making sure anybody who can create facilities sees the real (non-cached) data
        """
        if not "facility_exists" in request.session or request.is_admin:  
            request.session["facility_count"] = Facility.objects.count()
            request.session["facility_exists"] = request.session["facility_count"] > 0

