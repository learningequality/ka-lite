from annoying.decorators import render_to

from django.conf import settings; logging = settings.LOG
from django.core.exceptions import ValidationError
from django.http import Http404

from kalite.main.models import UserLog
from kalite.shared.decorators.auth import require_authorized_access_to_student_data, require_authorized_admin, get_user_from_request
from kalite.facility.decorators import facility_from_request

@require_authorized_access_to_student_data
@render_to("coachreports/student_view.html")
def student_view(request):
    """
    Student view: data generated on the back-end.

    Student view lists a by-topic-summary of their activity logs.
    """
    return student_view_context(request=request)


@require_authorized_access_to_student_data
def student_view_context(request):
    """
    Context done separately, to be importable for similar pages.
    """
    user = get_user_from_request(request=request)
    if not user:
        raise Http404("User not found.")

    context = {
        "facility_id": user.facility.id,
        "student": user,
    }
    return context

@require_authorized_admin
@facility_from_request
@render_to("coachreports/coach.html")
def coach_reports(request, facility=None):
    """Landing page needs plotting context in order to generate the navbar"""
    if facility:
        facility_id = facility.id
    else:
        facility_id = None
    return {
        "facility_id": facility_id
        }



def log_coach_report_view(request):
    """Record coach report view by teacher"""
    if "facility_user" in request.session:
        try:
            # Log a "begin" and end here
            user = request.session["facility_user"]
            UserLog.begin_user_activity(user, activity_type="coachreport")
            UserLog.update_user_activity(user, activity_type="login")  # to track active login time for teachers
            UserLog.end_user_activity(user, activity_type="coachreport")
        except ValidationError as e:
            # Never report this error; don't want this logging to block other functionality.
            logging.error("Failed to update Teacher userlog activity login: %s" % e)
