from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

import settings

def is_static_file(path):
    return path.startswith(settings.STATIC_URL) or path.startswith(settings.MEDIA_URL)

class LinkUserManual:
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if request.path == reverse("homepage"):
            messages.info(request, mark_safe(_("Welcome to our demo server!"
                "  Please visit our <a href='http://kalitewiki.learningequality.org/user-s-manual/using-ka-lite'>user's manual</a> or <a href='http://kalite.learningequality.org/'>homepage</a> for more information."
            )))

class ShowAdminLogin:
    def process_request(self, request):
        if is_static_file(request.path):
            return
        if not request.is_logged_in:
            messages.info(request, mark_safe(_("<a href='%(sign_up_url)s'>Sign up as a student</a>, or <a href='%(log_in_url)s'>log in</a> as the site-wide admin (username=%(user_name)s, password=%(passwd)s)" % {
                "sign_up_url": reverse("add_facility_student"),
                "log_in_url": reverse("login"),
                "user_name": settings.DEMO_ADMIN_USERNAME,
                "passwd": settings.DEMO_ADMIN_PASSWORD,
            })))

class StopAdminAccess:
    def process_request(self, request):
        if request.path.startswith(reverse("admin:index")):
            messages.error(request, _("The admin interface is disabled in the demo server."))
            raise PermissionDenied("Admin interface is disabled in the demo server.")